from django.urls import path
from .views import mostrar_accountinfo, mostrar_reportes
from . import views
from .views import CustomLoginView, register
from .views import logout_view

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),
    path('register/', register, name='register'),  # Vista de registro
    path('accountinfo/', mostrar_accountinfo, name='accountinfo'),
    path('logout/', logout_view, name='logout'),
    
    path('actualizar_tags/', views.actualizar_tags, name='actualizar_tags'),
    path('reportes/', mostrar_reportes, name='mostrar_reportes'),
    path('descargar_registros/', views.descargar_registros, name='descargar_registros'),
    path('exportar-reportes/', views.exportar_reportes, name='exportar_reportes'),
    
    
]
