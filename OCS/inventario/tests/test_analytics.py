"""
test_analytics.py — Unit tests for the AI Analytics Engine.

Tests anomaly detection, data quality scoring, distribution analysis,
and prediction generation using synthetic asset data.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

from inventario.services.analytics import (
    AssetAnalyticsEngine,
    AnalyticsResult,
    Anomaly,
    DataQualityReport,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_assets(n=50, tag_rate=0.7, mv_rate=0.1, dupe_rate=0.05):
    """Generate synthetic asset data as a list of dicts."""
    assets = []
    buildings = ["EDIF-A", "EDIF-B", "EDIF-C", "EDIF-D", "TELCO"]
    used_inventarios = []

    for i in range(n):
        hw_id = f"HW-{i+1:04d}"
        is_mv = np.random.random() < mv_rate
        has_tag = np.random.random() < tag_rate

        if is_mv:
            inventario = "MV"
            tag = ""
            edificio = ""
        else:
            inventario = f"INV-{i+1:06d}"
            # Inject duplicates
            if used_inventarios and np.random.random() < dupe_rate:
                inventario = np.random.choice(used_inventarios)
            used_inventarios.append(inventario)

            if has_tag:
                bldg = np.random.choice(buildings)
                local = f"{np.random.randint(100, 999)}"
                tag = f"{bldg.split('-')[-1]}-{local}"
                edificio = bldg
            else:
                tag = ""
                edificio = ""

        assets.append({
            "hardware_id": hw_id,
            "tag": tag if tag else None,
            "edificio": edificio if edificio else None,
            "noinventario": inventario,
            "usuario": f"user_{i}" if not is_mv else None,
            "observaciones": None,
            "fields_3": inventario,
        })
    return assets


def make_df(assets):
    """Convert asset list to DataFrame."""
    return pd.DataFrame(assets)


# ---------------------------------------------------------------------------
# Tests: Anomaly Detection
# ---------------------------------------------------------------------------
class TestAnomalyDetection:
    """Tests for the anomaly detection module."""

    def test_detects_duplicates(self):
        """Duplicate inventory numbers should raise a critical anomaly."""
        engine = AssetAnalyticsEngine()
        assets = make_assets(30, tag_rate=0.8, dupe_rate=0.0)
        # Inject explicit duplicate
        assets[0]["fields_3"] = "INV-DUPE"
        assets[1]["fields_3"] = "INV-DUPE"
        df = make_df(assets)

        engine._detect_duplicates(df)
        dupes = [a for a in engine.result.anomalies if a.category == "duplicate"]
        assert len(dupes) >= 1
        assert dupes[0].severity == "critical"

    def test_no_false_duplicate_on_mv(self):
        """MV entries should not be flagged as duplicates."""
        engine = AssetAnalyticsEngine()
        assets = [
            {"hardware_id": "1", "tag": "", "edificio": "", "noinventario": "MV",
             "usuario": "", "observaciones": "", "fields_3": "MV"},
            {"hardware_id": "2", "tag": "", "edificio": "", "noinventario": "MV",
             "usuario": "", "observaciones": "", "fields_3": "MV"},
        ]
        df = make_df(assets)
        engine._detect_duplicates(df)
        assert len(engine.result.anomalies) == 0

    def test_detects_missing_tags(self):
        """Assets without TAGs should be detected."""
        engine = AssetAnalyticsEngine()
        assets = make_assets(20, tag_rate=0.0)
        df = make_df(assets)

        engine._detect_missing_tags(df)
        missing = [a for a in engine.result.anomalies if a.category == "missing_tag"]
        assert len(missing) >= 1

    def test_detects_orphan_assets(self):
        """Assets with no tag, edificio, or usuario should be flagged."""
        engine = AssetAnalyticsEngine()
        assets = [
            {"hardware_id": "ORPHAN-1", "tag": None, "edificio": None,
             "noinventario": "", "usuario": None, "observaciones": None,
             "fields_3": None},
        ]
        df = make_df(assets)
        engine._detect_orphan_assets(df)
        orphans = [a for a in engine.result.anomalies if a.category == "orphan"]
        assert len(orphans) == 1

    def test_no_anomalies_on_clean_data(self):
        """Clean, well-tagged data should produce no critical anomalies."""
        engine = AssetAnalyticsEngine()
        assets = []
        for i in range(10):
            assets.append({
                "hardware_id": f"HW-{i}",
                "tag": f"A-{100+i}",
                "edificio": "Edificio A",
                "noinventario": f"INV-{i:06d}",
                "usuario": f"user_{i}",
                "observaciones": None,
                "fields_3": f"INV-{i:06d}",
            })
        df = make_df(assets)
        engine._detect_anomalies(df)
        critical = [a for a in engine.result.anomalies if a.severity == "critical"]
        assert len(critical) == 0


# ---------------------------------------------------------------------------
# Tests: Data Quality Scoring
# ---------------------------------------------------------------------------
class TestDataQuality:
    """Tests for the data quality scoring module."""

    def test_perfect_data_quality(self):
        """All fields filled, consistent TAGs, unique inventories → high score."""
        engine = AssetAnalyticsEngine()
        assets = []
        for i in range(10):
            assets.append({
                "hardware_id": f"HW-{i}",
                "tag": f"EDIF-{100+i}",
                "edificio": "Edificio A",
                "noinventario": f"INV-{i:06d}",
                "usuario": f"user_{i}",
                "observaciones": "OK",
                "fields_3": f"INV-{i:06d}",
            })
        df = make_df(assets)
        engine._compute_data_quality(df)
        assert engine.result.data_quality.score >= 70
        assert engine.result.data_quality.grade in ("A", "B", "C")

    def test_empty_data(self):
        """Empty DataFrame should produce grade F."""
        engine = AssetAnalyticsEngine()
        df = make_df([])
        engine._compute_data_quality(df)
        assert engine.result.data_quality.grade == "F"
        assert engine.result.data_quality.score == 0

    def test_grade_computation(self):
        """Test the grade computing static method."""
        assert DataQualityReport.compute_grade(95) == "A"
        assert DataQualityReport.compute_grade(85) == "B"
        assert DataQualityReport.compute_grade(75) == "C"
        assert DataQualityReport.compute_grade(65) == "D"
        assert DataQualityReport.compute_grade(45) == "F"


# ---------------------------------------------------------------------------
# Tests: Distribution Analysis
# ---------------------------------------------------------------------------
class TestDistributions:
    """Tests for the distribution analysis module."""

    def test_tag_status_distribution(self):
        """Should correctly categorize assets by TAG status."""
        engine = AssetAnalyticsEngine()
        assets = [
            {"hardware_id": "1", "tag": "A-100", "edificio": "A",
             "noinventario": "INV-1", "usuario": "u1",
             "observaciones": None, "fields_3": "INV-1"},
            {"hardware_id": "2", "tag": None, "edificio": "",
             "noinventario": "", "usuario": "u2",
             "observaciones": None, "fields_3": None},
            {"hardware_id": "3", "tag": "", "edificio": "",
             "noinventario": "MV", "usuario": "",
             "observaciones": None, "fields_3": "MV"},
        ]
        df = make_df(assets)
        engine._analyze_distributions(df)

        dist = engine.result.distribution["tag_status"]
        assert dist["Con TAG"] == 1
        assert dist["Máquinas Virtuales"] == 1

    def test_building_distribution(self):
        """Should count assets per building from TAG prefix."""
        engine = AssetAnalyticsEngine()
        assets = [
            {"hardware_id": str(i), "tag": f"EDIF-{100+i}", "edificio": "EDIF",
             "noinventario": f"INV-{i}", "usuario": f"u{i}",
             "observaciones": None, "fields_3": f"INV-{i}"}
            for i in range(5)
        ]
        df = make_df(assets)
        engine._analyze_distributions(df)
        assert "EDIF" in engine.result.distribution.get("buildings", {})


# ---------------------------------------------------------------------------
# Tests: Predictions
# ---------------------------------------------------------------------------
class TestPredictions:
    """Tests for the prediction and recommendation engine."""

    def test_generates_sync_recommendation(self):
        """Assets without TAGs should trigger sync recommendation."""
        engine = AssetAnalyticsEngine()
        assets = make_assets(20, tag_rate=0.3)
        df = make_df(assets)

        engine._detect_anomalies(df)
        engine._compute_data_quality(df)
        engine._analyze_distributions(df)
        engine._generate_predictions(df)

        recs = engine.result.predictions.get("recommendations", [])
        sync_recs = [r for r in recs if "sincronización" in r["action"].lower()]
        assert len(sync_recs) >= 1

    def test_coverage_projection(self):
        """Should compute coverage gap to 95% target."""
        engine = AssetAnalyticsEngine()
        assets = make_assets(100, tag_rate=0.5)
        df = make_df(assets)

        engine._detect_anomalies(df)
        engine._compute_data_quality(df)
        engine._analyze_distributions(df)
        engine._generate_predictions(df)

        assert "coverage" in engine.result.predictions
        assert engine.result.predictions["coverage"]["target_pct"] == 95.0


# ---------------------------------------------------------------------------
# Tests: Full Pipeline
# ---------------------------------------------------------------------------
class TestFullPipeline:
    """Integration tests for the complete analytics pipeline."""

    @patch("inventario.services.analytics.AccountInfo")
    def test_full_analysis_with_mocked_db(self, mock_model):
        """Full pipeline should run and return AnalyticsResult."""
        assets = make_assets(50, tag_rate=0.6, dupe_rate=0.1)
        mock_model.objects.all.return_value.values.return_value = assets

        engine = AssetAnalyticsEngine()
        result = engine.run_full_analysis()

        assert isinstance(result, AnalyticsResult)
        assert result.data_quality is not None
        assert result.summary["total_assets"] == 50
        assert len(result.anomalies) >= 0

    @patch("inventario.services.analytics.AccountInfo")
    def test_empty_database(self, mock_model):
        """Should handle empty database gracefully."""
        mock_model.objects.all.return_value.values.return_value = []

        engine = AssetAnalyticsEngine()
        result = engine.run_full_analysis()

        assert result.summary["total"] == 0


# ---------------------------------------------------------------------------
# Tests: Data Classes
# ---------------------------------------------------------------------------
class TestDataClasses:
    """Tests for the data class helpers."""

    def test_anomaly_properties(self):
        """Test Anomaly color and icon properties."""
        a = Anomaly(
            severity="critical",
            category="duplicate",
            title="Test",
            description="Desc",
        )
        assert a.color == "danger"
        assert "triangle" in a.icon

        b = Anomaly(severity="info", category="pattern", title="T", description="D")
        assert b.color == "info"

    def test_analytics_result_timestamp(self):
        """Result should have a timestamp."""
        result = AnalyticsResult()
        assert result.generated_at is not None
        assert "T" in result.generated_at  # ISO format
