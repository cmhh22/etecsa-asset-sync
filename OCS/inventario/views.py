"""
views.py — Django views for ETECSA Asset Sync.

Provides views for the asset dashboard, TAG synchronization,
report viewing, AI analytics, authentication, and data export.
"""

import os
import logging
from dataclasses import asdict

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.management import call_command
from django.db.models import Q
from django.http import FileResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import AccountInfo
from .forms import LoginForm, RegistroForm
from .services.analytics import AssetAnalyticsEngine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@login_required
def dashboard(request):
    """Main dashboard with summary statistics and charts."""
    cuentas = AccountInfo.objects.all()
    total = cuentas.count()

    with_tag = cuentas.exclude(tag__isnull=True).exclude(tag="").count()
    without_tag = total - with_tag
    virtual_machines = cuentas.filter(fields_3="MV").count()
    empty_inventory = cuentas.filter(
        Q(fields_3__isnull=True) | Q(fields_3="")
    ).count()

    # Assets by building (from TAG field: "Edificio-Local")
    buildings = {}
    for cuenta in cuentas.exclude(tag__isnull=True).exclude(tag=""):
        building = cuenta.tag.split("-")[0] if "-" in cuenta.tag else cuenta.tag
        buildings[building] = buildings.get(building, 0) + 1

    buildings_sorted = dict(
        sorted(buildings.items(), key=lambda x: x[1], reverse=True)[:10]
    )

    context = {
        "total_assets": total,
        "with_tag": with_tag,
        "without_tag": without_tag,
        "virtual_machines": virtual_machines,
        "empty_inventory": empty_inventory,
        "tag_percentage": round((with_tag / total * 100) if total else 0, 1),
        "building_labels": list(buildings_sorted.keys()),
        "building_counts": list(buildings_sorted.values()),
        "recent_assets": cuentas.order_by("-hardware_id")[:5],
    }
    return render(request, "dashboard.html", context)


# ---------------------------------------------------------------------------
# Asset Table
# ---------------------------------------------------------------------------
@login_required
def mostrar_accountinfo(request):
    """Display the full asset inventory table."""
    cuentas = AccountInfo.objects.all()
    return render(request, "accountinfo.html", {"cuentas": cuentas})


# ---------------------------------------------------------------------------
# Sync Tags
# ---------------------------------------------------------------------------
@csrf_exempt
@login_required
def actualizar_tags(request):
    """Execute TAG synchronization via the management command."""
    if request.method == "POST":
        try:
            call_command("sync_tags")
            messages.success(request, "TAGs actualizados con éxito.")
        except Exception as e:
            logger.error(f"Error en sincronización: {e}")
            messages.error(request, f"Error al actualizar TAGs: {e}")
        return HttpResponseRedirect(reverse("accountinfo"))
    return redirect("accountinfo")


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
@login_required
def mostrar_reportes(request):
    """View generated Excel reports with sheet selector."""
    excel_path = os.path.join(settings.BASE_DIR, "Reportes.xlsx")

    try:
        hojas = pd.ExcelFile(excel_path).sheet_names
        hoja_seleccionada = request.GET.get("hoja", hojas[0])
        df = pd.read_excel(excel_path, sheet_name=hoja_seleccionada)
        filas = df.to_dict(orient="records")

        sheet_counts = {}
        for hoja in hojas:
            sheet_counts[hoja] = len(pd.read_excel(excel_path, sheet_name=hoja))

        return render(request, "reportes.html", {
            "filas": filas,
            "hojas": hojas,
            "hoja_seleccionada": hoja_seleccionada,
            "sheet_counts": sheet_counts,
            "total_filas": len(filas),
        })
    except FileNotFoundError:
        return render(request, "no_reportes.html")
    except Exception as e:
        logger.error(f"Error leyendo reportes: {e}")
        return render(request, "no_reportes.html")


@login_required
def descargar_registros(request):
    """Download the sync log file."""
    filepath = os.path.join(settings.BASE_DIR, "Registros.txt")
    if os.path.exists(filepath):
        return FileResponse(
            open(filepath, "rb"), as_attachment=True, filename="Registros.txt"
        )
    messages.warning(request, "No hay registros disponibles.")
    return redirect("accountinfo")


@login_required
def exportar_reportes(request):
    """Download the generated Excel report."""
    excel_path = os.path.join(settings.BASE_DIR, "Reportes.xlsx")
    if os.path.exists(excel_path):
        return FileResponse(
            open(excel_path, "rb"), as_attachment=True, filename="Reportes.xlsx"
        )
    return render(request, "no_reportes.html", {"mensaje": "Aún no hay reportes generados."})


# ---------------------------------------------------------------------------
# API endpoint for dashboard charts (AJAX)
# ---------------------------------------------------------------------------
@login_required
def api_dashboard_stats(request):
    """Return dashboard statistics as JSON for dynamic charts."""
    cuentas = AccountInfo.objects.all()
    total = cuentas.count()
    with_tag = cuentas.exclude(tag__isnull=True).exclude(tag="").count()

    buildings = {}
    for c in cuentas.exclude(tag__isnull=True).exclude(tag=""):
        b = c.tag.split("-")[0] if "-" in c.tag else c.tag
        buildings[b] = buildings.get(b, 0) + 1

    return JsonResponse({
        "total": total,
        "with_tag": with_tag,
        "without_tag": total - with_tag,
        "virtual_machines": cuentas.filter(fields_3="MV").count(),
        "empty_inventory": cuentas.filter(Q(fields_3__isnull=True) | Q(fields_3="")).count(),
        "buildings": buildings,
    })


# ---------------------------------------------------------------------------
# AI Analytics
# ---------------------------------------------------------------------------
@login_required
def analytics_view(request):
    """AI-powered analytics dashboard with anomaly detection and data quality."""
    engine = AssetAnalyticsEngine()
    result = engine.run_full_analysis()
    result_dict = asdict(result)

    context = {
        "anomalies": result.anomalies,
        "data_quality": result.data_quality,
        "distribution": result.distribution,
        "predictions": result.predictions,
        "summary": result.summary,
        "result_json": result_dict,
    }
    return render(request, "analytics.html", context)


@login_required
def api_analytics(request):
    """Return full AI analytics results as JSON."""
    engine = AssetAnalyticsEngine()
    result = engine.run_full_analysis()
    return JsonResponse(asdict(result), safe=False)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
class CustomLoginView(LoginView):
    template_name = "login.html"

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Nombre de usuario o contraseña incorrectos.")
            return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


def register(request):
    """User registration view."""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        try:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect("dashboard")
        except Exception as e:
            messages.error(request, f"Error al registrar: {e}")
    return render(request, "register.html")


def logout_view(request):
    """Log out and redirect to login."""
    logout(request)
    return redirect("login")