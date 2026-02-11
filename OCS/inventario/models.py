from django.db import models

class AccountInfo(models.Model):
    hardware_id = models.CharField(max_length=100, primary_key=True)
    tag = models.CharField(max_length=100)
    edificio = models.CharField(max_length=100)
    noinventario = models.CharField(max_length=100)
    usuario = models.CharField(max_length=100)
    observaciones = models.TextField(blank=True, null=True)
    fields_3 = models.CharField(max_length=100, blank=True, null=True)
    fields_4 = models.CharField(max_length=100, blank=True, null=True)
    fields_5 = models.CharField(max_length=100, blank=True, null=True)
    fields_6 = models.CharField(max_length=100, blank=True, null=True)
    fields_7 = models.CharField(max_length=100, blank=True, null=True)
    fields_8 = models.CharField(max_length=100, blank=True, null=True)
    fields_9 = models.CharField(max_length=100, blank=True, null=True)
    fields_10 = models.CharField(max_length=100, blank=True, null=True)
    fields_11 = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'accountinfo'  # Asegúrate de que coincida con el nombre de la tabla existente

    def __str__(self):
        return f"{self.tag} - {self.usuario}"

class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.username


# Municipality Table
class Municipio(models.Model):
    nombre_municipio = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre_municipio

# Building (Edificio) Table
class Edificio(models.Model):
    nombre_edificio = models.CharField(max_length=255)
    municipio = models.ForeignKey(Municipio, related_name='edificios', on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre_edificio

# Department (Departamento) Table
class Departamento(models.Model):
    nombre_departamento = models.CharField(max_length=255)
    abreviatura = models.CharField(max_length=10)

    def __str__(self):
        return self.nombre_departamento

# Locales Table
class Local(models.Model):
    numero_local = models.CharField(max_length=50, unique=True)
    descripcion_local = models.TextField()
    edificio = models.ForeignKey(Edificio, related_name='locales', on_delete=models.CASCADE)
    departamento = models.ForeignKey(Departamento, related_name='locales', on_delete=models.CASCADE)

    def __str__(self):
        return self.numero_local

# Centro de Costo Table
class CentroCosto(models.Model):
    numero_centro_costo = models.CharField(max_length=50, unique=True)
    area = models.CharField(max_length=255)
    responsable = models.CharField(max_length=255)
    local = models.ForeignKey(Local, related_name='centros_de_costo', on_delete=models.CASCADE)

    def __str__(self):
        return self.numero_centro_costo
