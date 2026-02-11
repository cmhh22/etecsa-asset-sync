from django.urls import path
from . import views
from .views import CustomLoginView

urlpatterns = [
    # Auth
    path('', CustomLoginView.as_view(), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Assets
    path('accountinfo/', views.mostrar_accountinfo, name='accountinfo'),
    path('actualizar_tags/', views.actualizar_tags, name='actualizar_tags'),

    # Reports
    path('reportes/', views.mostrar_reportes, name='mostrar_reportes'),
    path('descargar_registros/', views.descargar_registros, name='descargar_registros'),
    path('exportar-reportes/', views.exportar_reportes, name='exportar_reportes'),

    # API
    path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/analytics/', views.api_analytics, name='api_analytics'),

    # AI Analytics
    path('analytics/', views.analytics_view, name='analytics'),
]
