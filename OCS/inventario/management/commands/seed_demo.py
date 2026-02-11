"""
seed_demo — Populate the database with fictional demo data.

Creates sample assets, buildings, and a superuser so reviewers
can explore the application without needing real ETECSA data.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --reset   # Wipe existing data first
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from inventario.models import AccountInfo, Edificio, Municipio


class Command(BaseCommand):
    help = "Seed database with fictional demo data for ETECSA Asset Sync"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo data before seeding",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            AccountInfo.objects.all().delete()
            Edificio.objects.all().delete()
            Municipio.objects.all().delete()
            self.stdout.write(self.style.WARNING("Existing data cleared."))

        # --- Superuser ---
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@etecsa.cu", "admin123")
            self.stdout.write(self.style.SUCCESS("Superuser created: admin / admin123"))
        else:
            self.stdout.write("Superuser 'admin' already exists.")

        # --- Locations ---
        mun_cfg, _ = Municipio.objects.get_or_create(nombre_municipio="Cienfuegos")
        mun_rod, _ = Municipio.objects.get_or_create(nombre_municipio="Rodas")
        mun_cru, _ = Municipio.objects.get_or_create(nombre_municipio="Cruces")
        mun_pal, _ = Municipio.objects.get_or_create(nombre_municipio="Palmira")

        buildings = {
            "DTCFG": mun_cfg,
            "CCFG_CENTRO": mun_cfg,
            "CCFG_PRADO": mun_cfg,
            "MUN_RODAS": mun_rod,
            "MUN_CRUCES": mun_cru,
            "MUN_PALMIRA": mun_pal,
        }
        for name, mun in buildings.items():
            Edificio.objects.get_or_create(
                nombre_edificio=name, defaults={"municipio": mun}
            )

        # --- Assets ---
        # Tuples: (hw_id, tag, edificio, inventario, usuario, fields_3)
        demo_assets = [
            ("1001", "DTCFG-Despacho Dir", "DTCFG", "180045", "Juan Perez", "180045"),
            ("1002", "DTCFG-Contabilidad", "DTCFG", "180046", "Maria Garcia", "180046"),
            ("1003", "CCFG_CENTRO-RRHH", "CCFG_CENTRO", "180047", "Carlos Lopez", "180047"),
            ("1004", "CCFG_PRADO-Comercial", "CCFG_PRADO", "180048", "Ana Rodriguez", "180048"),
            ("1005", "DTCFG-Area Tecnica", "DTCFG", "180049", "Pedro Sanchez", "180049"),
            ("1006", "DTCFG-Direccion", "DTCFG", "180050", "Director Provincial", "180050"),
            ("1007", "MUN_RODAS-Oficina", "MUN_RODAS", "180051", "Luis Hernandez", "180051"),
            ("1008", "MUN_CRUCES-Oficina", "MUN_CRUCES", "180052", "Sofia Martinez", "180052"),
            ("1009", "DTCFG-Datacenter", "DTCFG", "180054", "Admin Sistemas", "180054"),
            ("1010", "CCFG_CENTRO-Almacen", "CCFG_CENTRO", "180055", "Teresa Gomez", "180055"),
            ("1011", "DTCFG-Juridico", "DTCFG", "180056", "Fernando Ruiz", "180056"),
            ("1012", "", "", "180057", "Test VM", "MV"),
            ("1013", "CCFG_PRADO-Recepcion", "CCFG_PRADO", "180058", "Marta Suarez", "180058"),
            ("1014", "DTCFG-Taller", "DTCFG", "180059", "Miguel Torres", "180059"),
            # Duplicate inventory number (anomaly)
            ("1015", "DTCFG-Despacho Dir", "DTCFG", "180045", "Juan Perez", "180045"),
            # Empty inventory (anomaly)
            ("1016", "DTCFG-SinDoc", "DTCFG", "", "Sin Inventario", ""),
            # Missing TAG (anomaly)
            ("1017", "", "", "180060", "Nuevo Equipo", "180060"),
            ("1018", "CCFG_CENTRO-Planificacion", "CCFG_CENTRO", "180061", "Laura Vega", "180061"),
            ("1019", "MUN_CRUCES-Comercial", "MUN_CRUCES", "180062", "Diego Mora", "180062"),
            # Orphan asset — no tag, no building (anomaly)
            ("1020", "", "", "180063", "Roberto Diaz", "180063"),
        ]

        created = 0
        for hw_id, tag, edif, inv, user, f3 in demo_assets:
            _, was_created = AccountInfo.objects.get_or_create(
                hardware_id=hw_id,
                defaults={
                    "tag": tag,
                    "edificio": edif,
                    "noinventario": inv,
                    "usuario": user,
                    "fields_3": f3,
                },
            )
            if was_created:
                created += 1

        total = AccountInfo.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data seeded: {created} new assets (total: {total})"
            )
        )
        self.stdout.write(
            f"  Municipios: {Municipio.objects.count()}, "
            f"Edificios: {Edificio.objects.count()}"
        )
        self.stdout.write(
            self.style.SUCCESS(
                "\nReady! Log in at http://localhost:8000 with admin / admin123"
            )
        )
