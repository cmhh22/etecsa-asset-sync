"""
test_models.py — Tests for ETECSA Asset Sync Django models.
"""

from django.test import TestCase
from inventario.models import (
    AccountInfo,
    Municipio,
    Edificio,
    Departamento,
    Local,
    CentroCosto,
)


class TestAccountInfoModel(TestCase):
    """Tests for the AccountInfo model."""

    def test_str_representation(self):
        """Should return 'tag - usuario' string."""
        asset = AccountInfo(
            hardware_id="HW-001",
            tag="EDIF-101",
            edificio="Edificio A",
            noinventario="INV-000001",
            usuario="jperez",
        )
        self.assertEqual(str(asset), "EDIF-101 - jperez")

    def test_meta_db_table(self):
        """Model should map to 'accountinfo' table."""
        self.assertEqual(AccountInfo._meta.db_table, "accountinfo")


class TestLocationModels(TestCase):
    """Tests for the location hierarchy models."""

    def setUp(self):
        self.municipio = Municipio.objects.create(nombre_municipio="Cienfuegos")
        self.edificio = Edificio.objects.create(
            nombre_edificio="Edificio Central", municipio=self.municipio
        )
        self.departamento = Departamento.objects.create(
            nombre_departamento="Informática", abreviatura="INF"
        )
        self.local = Local.objects.create(
            numero_local="LOC-001",
            descripcion_local="Sala de servidores",
            edificio=self.edificio,
            departamento=self.departamento,
        )
        self.centro = CentroCosto.objects.create(
            numero_centro_costo="CC-001",
            area="IT",
            responsable="Admin",
            local=self.local,
        )

    def test_municipio_str(self):
        self.assertEqual(str(self.municipio), "Cienfuegos")

    def test_edificio_str(self):
        self.assertEqual(str(self.edificio), "Edificio Central")

    def test_edificio_municipio_relation(self):
        self.assertEqual(self.edificio.municipio, self.municipio)

    def test_departamento_str(self):
        self.assertEqual(str(self.departamento), "Informática")

    def test_local_str(self):
        self.assertEqual(str(self.local), "LOC-001")

    def test_local_relations(self):
        self.assertEqual(self.local.edificio, self.edificio)
        self.assertEqual(self.local.departamento, self.departamento)

    def test_centro_costo_str(self):
        self.assertEqual(str(self.centro), "CC-001")

    def test_centro_costo_local_relation(self):
        self.assertEqual(self.centro.local, self.local)

    def test_cascade_delete(self):
        """Deleting municipio should cascade to edificio → local → centro."""
        self.municipio.delete()
        self.assertEqual(Edificio.objects.count(), 0)
        self.assertEqual(Local.objects.count(), 0)
        self.assertEqual(CentroCosto.objects.count(), 0)
