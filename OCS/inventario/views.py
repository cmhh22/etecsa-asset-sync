import os
import subprocess
from turtle import pd
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render,redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import AccountInfo
from django.contrib import messages  # Importa el sistema de mensajes
import pandas as pd  # Asegúrate de que esta línea esté aquí
import openpyxl
from django.contrib.auth.views import LoginView
from .forms import LoginForm
from .forms import RegistroForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout

#@login_required
def mostrar_accountinfo(request):
    cuentas = AccountInfo.objects.all()
    return render(request, 'accountinfo.html', {'cuentas': cuentas})

@csrf_exempt
def actualizar_tags(request):
    if request.method == 'POST':
        # Ejecuta tu script, asumiendo que está al mismo nivel que manage.py
        subprocess.call(['python', 'script_actualizar_TAG.py'])  # Cambia 'tu_script.py' por el nombre correcto

        # Agrega un mensaje de éxito
        messages.success(request, 'TAGs actualizados con éxito.')
        
        # Redirigir después de ejecutar el script a la misma página con la tabla
        return HttpResponseRedirect(reverse('accountinfo'))

def mostrar_reportes(request):
    # Ruta al archivo de Excel
    excel_path = os.path.join(settings.BASE_DIR, 'Reportes.xlsx')

    try:
        # Intentar leer el archivo Excel
        hojas = pd.ExcelFile(excel_path).sheet_names
        hoja_seleccionada = request.GET.get('hoja', hojas[0])  # Seleccionar la primera hoja por defecto
        filas = pd.read_excel(excel_path, sheet_name=hoja_seleccionada).to_dict(orient='records')
        return render(request, 'reportes.html', {'filas': filas, 'hojas': hojas, 'hoja_seleccionada': hoja_seleccionada})
    
    except FileNotFoundError:
        # En caso de que el archivo no exista, mostrar una página de advertencia
        return render(request, 'no_reportes.html')

    except Exception as e:
        # Otras excepciones se pueden manejar aquí (opcional)
        return render(request, 'error.html', {'error': str(e)})

def descargar_registros(request):
    filepath = os.path.join(os.path.dirname(__file__), '..', 'Registros.txt')
    return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='Registros.txt')

def exportar_reportes(request):
    # Ruta completa al archivo de Excel
    excel_path = os.path.join(settings.BASE_DIR, 'Reportes.xlsx')

    # Verificar si el archivo existe
    if os.path.exists(excel_path):
        # Si el archivo existe, se descarga
        response = FileResponse(open(excel_path, 'rb'), as_attachment=True, filename='Reportes.xlsx')
        return response
    else:
        # Si el archivo no existe, mostrar un mensaje de advertencia
        return render(request, 'no_reportes.html', {'mensaje': 'Aún no hay reportes generados.'})
    
class CustomLoginView(LoginView):
    template_name = 'login.html'  # Asegúrate de que este sea el nombre correcto de tu template
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('accountinfo')  # Redirige a la página de accountinfo
        else:
            messages.error(request, "Nombre de usuario o contraseña incorrectos.")
            return self.get(request, *args, **kwargs)  # Muestra el formulario nuevamente con el mensaje de error

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # Crear un nuevo usuario
            user = User.objects.create_user(username=username, password=password)
            user.save()
            login(request, user)  # Iniciar sesión automáticamente después de registrarse
            return redirect('accountinfo')  # Cambia a la URL correspondiente

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('accountinfo')  # Redirigir a la página de cuenta
        else:
            return JsonResponse({'success': False, 'error': 'Credenciales inválidas'})

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')  # Redirige a la página de inicio de sesión después de cerrar sesión