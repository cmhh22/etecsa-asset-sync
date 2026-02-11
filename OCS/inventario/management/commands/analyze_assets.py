"""
Django management command: analyze_assets

Runs the AI analytics engine to detect anomalies, compute data quality,
and generate recommendations for the IT asset database.

Usage:
    python manage.py analyze_assets
    python manage.py analyze_assets --json
    python manage.py analyze_assets --output report.json
"""

import json
import logging
from dataclasses import asdict

from django.core.management.base import BaseCommand

from inventario.services.analytics import AssetAnalyticsEngine

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run AI-powered analytics on the asset database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output results as JSON instead of formatted text.",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Save results to a JSON file.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n🔬 ETECSA Asset Sync — AI Analytics Engine\n"
        ))
        self.stdout.write("=" * 55)

        engine = AssetAnalyticsEngine()
        result = engine.run_full_analysis()

        if options["json"]:
            self._output_json(result)
        else:
            self._output_formatted(result)

        if options["output"]:
            filepath = options["output"]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(asdict(result), f, ensure_ascii=False, indent=2)
            self.stdout.write(self.style.SUCCESS(f"\n📄 Resultados guardados en: {filepath}"))

    def _output_formatted(self, result):
        # Summary
        s = result.summary
        self.stdout.write(f"\n📊 Resumen General")
        self.stdout.write(f"   Total de activos:    {s.get('total_assets', 0)}")
        self.stdout.write(f"   Anomalías detectadas: {s.get('total_anomalies', 0)}")
        self.stdout.write(f"     → Críticas:  {s.get('critical_anomalies', 0)}")
        self.stdout.write(f"     → Advertencias: {s.get('warning_anomalies', 0)}")

        # Data Quality
        dq = result.data_quality
        if dq:
            grade_colors = {
                "A": self.style.SUCCESS,
                "B": self.style.SUCCESS,
                "C": self.style.WARNING,
                "D": self.style.ERROR,
                "F": self.style.ERROR,
            }
            style = grade_colors.get(dq.grade, self.style.NOTICE)
            self.stdout.write(f"\n🏆 Calidad de Datos")
            self.stdout.write(f"   Puntuación: {style(f'{dq.score:.1f}/100 (Grado {dq.grade})')}")
            self.stdout.write(f"   Completitud:   {dq.completeness:.1f}%")
            self.stdout.write(f"   Consistencia:  {dq.consistency:.1f}%")
            self.stdout.write(f"   Unicidad:      {dq.uniqueness:.1f}%")
            self.stdout.write(f"   Validez:       {dq.validity:.1f}%")

            if dq.issues:
                self.stdout.write(f"\n   Problemas detectados:")
                for issue in dq.issues:
                    self.stdout.write(f"     ⚠ {issue}")

        # Anomalies
        if result.anomalies:
            self.stdout.write(f"\n🚨 Anomalías Detectadas ({len(result.anomalies)})")
            for i, anomaly in enumerate(result.anomalies, start=1):
                severity_map = {
                    "critical": self.style.ERROR("CRÍTICO"),
                    "warning": self.style.WARNING("ADVERTENCIA"),
                    "info": self.style.NOTICE("INFO"),
                }
                level = severity_map.get(anomaly.severity, anomaly.severity)
                self.stdout.write(f"\n   [{level}] {anomaly.title}")
                self.stdout.write(f"   {anomaly.description}")
                if anomaly.suggestion:
                    self.stdout.write(f"   💡 {anomaly.suggestion}")
                if anomaly.affected_assets[:5]:
                    self.stdout.write(f"   Afectados: {', '.join(str(a) for a in anomaly.affected_assets[:5])}")

        # Predictions
        preds = result.predictions
        if "recommendations" in preds:
            self.stdout.write(f"\n💡 Recomendaciones ({len(preds['recommendations'])})")
            for rec in preds["recommendations"]:
                priority_style = {
                    "alta": self.style.ERROR,
                    "media": self.style.WARNING,
                    "baja": self.style.NOTICE,
                }
                pstyle = priority_style.get(rec["priority"], self.style.NOTICE)
                self.stdout.write(f"   [{pstyle(rec['priority'].upper())}] {rec['action']}")
                self.stdout.write(f"      → {rec['impact']}")

        if "coverage" in preds:
            cov = preds["coverage"]
            self.stdout.write(f"\n📈 Proyección de Cobertura")
            self.stdout.write(f"   Actual: {cov['current_pct']}% → Objetivo: {cov['target_pct']}%")
            self.stdout.write(f"   {cov['message']}")

        self.stdout.write("\n" + "=" * 55)
        self.stdout.write(self.style.SUCCESS("✅ Análisis completado."))

    def _output_json(self, result):
        output = asdict(result)
        self.stdout.write(json.dumps(output, ensure_ascii=False, indent=2))
