from django.contrib import admin
from .models import AccountInfo, Municipio, Edificio, Departamento, Local, CentroCosto


@admin.register(AccountInfo)
class AccountInfoAdmin(admin.ModelAdmin):
    list_display = ('hardware_id', 'tag', 'fields_3', 'edificio', 'usuario')
    search_fields = ('tag', 'fields_3', 'usuario', 'hardware_id')
    list_filter = ('tag', 'edificio')


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_municipio')
    search_fields = ('nombre_municipio',)


@admin.register(Edificio)
class EdificioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_edificio', 'municipio')
    list_filter = ('municipio',)
    search_fields = ('nombre_edificio',)


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_departamento', 'abreviatura')
    search_fields = ('nombre_departamento', 'abreviatura')


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('numero_local', 'descripcion_local', 'edificio', 'departamento')
    list_filter = ('edificio', 'departamento')
    search_fields = ('numero_local', 'descripcion_local')


@admin.register(CentroCosto)
class CentroCostoAdmin(admin.ModelAdmin):
    list_display = ('numero_centro_costo', 'area', 'responsable', 'local')
    search_fields = ('numero_centro_costo', 'area', 'responsable')
