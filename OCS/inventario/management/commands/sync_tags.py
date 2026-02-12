"""
Django management command: sync_tags

Usage:
    python manage.py sync_tags
    python manage.py sync_tags --dry-run
    python manage.py sync_tags --report-only
"""

import logging
import time

from django.core.management.base import BaseCommand, CommandError
from decouple import config

from inventario.services import (
    ExcelDataSources,
    TagSyncProcessor,
    ReportGenerator,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Synchronize TAG fields in OCS Inventory by cross-referencing "
        "the AR01 Finance report and the HR Locations Classifier."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run without updating the database (analysis only).",
        )
        parser.add_argument(
            "--report-only",
            action="store_true",
            help="Generate report from existing data without re-syncing.",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="Reports.xlsx",
            help="Output path for the Excel report (default: Reports.xlsx).",
        )

    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  ETECSA Asset Sync — TAG Synchronization"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        try:
            # Load Excel data sources
            data_sources = ExcelDataSources.load(
                finance_file=config("EXCEL_ECONOMIA", default="AR01-1.xlsx"),
                classifier_file=config(
                    "EXCEL_CLASIFICADOR",
                    default="CLASIFICADOR DE LOCALES -KARINA-1.xlsx",
                ),
            )
            self.stdout.write(f"  AR01 entries: {len(data_sources.df_finance)}")
            self.stdout.write(
                f"  Classifier entries: {len(data_sources.df_classifier)}"
            )

            # Run sync (using Django ORM - works with SQLite, MySQL, PostgreSQL, etc.)
            processor = TagSyncProcessor(
                data_sources=data_sources,
                db_config={},  # Not used - Django ORM handles connection
                table_name=config("TABLA_ACCOUNTINFO", default="accountinfo"),
                column_name=config("COLUMNA_INVENTARIO", default="fields_3"),
            )

            if options["dry_run"]:
                self.stdout.write(
                    self.style.WARNING("\n  [DRY RUN] No database changes will be made.\n")
                )

            result = processor.execute()

            # Print summary
            summary = result.summary
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("  Results:"))
            self.stdout.write(f"    Total processed:    {summary['total_processed']}")
            self.stdout.write(
                self.style.SUCCESS(f"    TAGs updated:       {summary['tags_updated']}")
            )
            self.stdout.write(f"    Empty inventory:    {summary['empty_inventory']}")
            self.stdout.write(f"    Virtual machines:   {summary['virtual_machines']}")
            self.stdout.write(
                self.style.WARNING(f"    Duplicates:         {summary['duplicates']}")
            )
            self.stdout.write(
                self.style.WARNING(f"    Not in AR01:        {summary['not_in_ar01']}")
            )
            self.stdout.write(
                self.style.WARNING(
                    f"    Not in classifier:  {summary['not_in_classifier']}"
                )
            )
            self.stdout.write(f"    AR01 not in DB:     {summary['ar01_not_in_db']}")

            # Generate report
            reporter = ReportGenerator(output_path=options["output"])
            report_path = reporter.generate(result)
            self.stdout.write(
                self.style.SUCCESS(f"\n  Report saved to: {report_path}")
            )

        except FileNotFoundError as e:
            raise CommandError(f"Excel file not found: {e}")
        except Exception as e:
            raise CommandError(f"Sync failed: {e}")

        elapsed = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(f"\n  Completed in {elapsed:.2f}s")
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
