"""
analytics.py — AI-powered analytics engine for ETECSA Asset Sync.

Provides anomaly detection, trend analysis, data quality scoring,
and predictive insights using statistical methods and heuristics.
"""

from __future__ import annotations

import logging
import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd

from inventario.models import AccountInfo

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class Anomaly:
    """Represents a detected anomaly in the asset database."""

    severity: str  # "critical", "warning", "info"
    category: str  # "duplicate", "missing_tag", "orphan", "pattern"
    title: str
    description: str
    affected_assets: list[str] = field(default_factory=list)
    suggestion: str = ""

    @property
    def icon(self) -> str:
        icons = {
            "critical": "bi-exclamation-triangle-fill",
            "warning": "bi-exclamation-circle-fill",
            "info": "bi-info-circle-fill",
        }
        return icons.get(self.severity, "bi-question-circle")

    @property
    def color(self) -> str:
        colors = {"critical": "danger", "warning": "warning", "info": "info"}
        return colors.get(self.severity, "secondary")


@dataclass
class DataQualityReport:
    """Overall data quality assessment."""

    score: float  # 0-100
    grade: str  # A, B, C, D, F
    completeness: float  # % of fields filled
    consistency: float  # % of consistent TAG formats
    uniqueness: float  # % of unique inventory numbers
    validity: float  # % of valid TAG formats
    issues: list[str] = field(default_factory=list)

    @classmethod
    def compute_grade(cls, score: float) -> str:
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        return "F"


@dataclass
class TrendPoint:
    """A single point in a trend analysis."""

    label: str
    value: float
    change: float = 0.0  # % change from previous


@dataclass
class AnalyticsResult:
    """Complete analytics report."""

    anomalies: list[Anomaly] = field(default_factory=list)
    data_quality: Optional[DataQualityReport] = None
    distribution: dict[str, Any] = field(default_factory=dict)
    predictions: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )


# ---------------------------------------------------------------------------
# Analytics Engine
# ---------------------------------------------------------------------------
class AssetAnalyticsEngine:
    """
    AI-powered analytics engine that detects anomalies, computes data
    quality scores, analyzes distributions, and generates predictions.

    Uses statistical methods (z-score, IQR, entropy) combined with
    domain-specific heuristics for IT asset management.
    """

    TAG_PATTERN_REGEX = r"^[A-Z]{2,5}-\d{3,4}$"

    def __init__(self):
        self.result = AnalyticsResult()

    def run_full_analysis(self) -> AnalyticsResult:
        """Execute the complete analytics pipeline."""
        logger.info("Starting AI analytics pipeline...")
        assets = list(
            AccountInfo.objects.all().values(
                "hardware_id", "tag", "edificio", "noinventario",
                "usuario", "observaciones", "fields_3",
            )
        )

        if not assets:
            logger.warning("No assets found for analysis.")
            self.result.summary = {"total": 0, "message": "No data"}
            return self.result

        df = pd.DataFrame(assets)

        # Run all analysis modules
        self._detect_anomalies(df)
        self._compute_data_quality(df)
        self._analyze_distributions(df)
        self._generate_predictions(df)
        self._build_summary(df)

        logger.info(
            f"Analytics complete: {len(self.result.anomalies)} anomalies, "
            f"quality score: {self.result.data_quality.score:.1f}"
        )
        return self.result

    # ------------------------------------------------------------------
    # Anomaly Detection
    # ------------------------------------------------------------------
    def _detect_anomalies(self, df: pd.DataFrame) -> None:
        """Run multi-strategy anomaly detection."""
        self._detect_duplicates(df)
        self._detect_missing_tags(df)
        self._detect_orphan_assets(df)
        self._detect_tag_pattern_anomalies(df)
        self._detect_building_outliers(df)

    def _detect_duplicates(self, df: pd.DataFrame) -> None:
        """Find duplicate inventory numbers (critical anomaly)."""
        inv_col = df["fields_3"].dropna()
        inv_col = inv_col[inv_col != "MV"].str.strip()
        dupes = inv_col[inv_col.duplicated(keep=False)]

        if not dupes.empty:
            dupe_counts = Counter(dupes.values)
            affected = [
                f"{inv} (x{count})" for inv, count in dupe_counts.items()
            ]
            self.result.anomalies.append(
                Anomaly(
                    severity="critical",
                    category="duplicate",
                    title="Duplicate inventory numbers",
                    description=(
                        f"{len(dupe_counts)} inventory numbers found "
                        f"assigned to multiple devices ({sum(dupe_counts.values())} "
                        f"records affected)."
                    ),
                    affected_assets=affected[:20],
                    suggestion=(
                        "Check the AR01 report for devices with duplicate inventory "
                        "numbers and correct the assignment in the database."
                    ),
                )
            )

    def _detect_missing_tags(self, df: pd.DataFrame) -> None:
        """Detect assets without TAG assignment."""
        no_tag = df[df["tag"].isna() | (df["tag"].str.strip() == "")]
        total = len(df)
        pct = (len(no_tag) / total * 100) if total else 0

        if len(no_tag) > 0:
            severity = "critical" if pct > 30 else "warning" if pct > 10 else "info"
            self.result.anomalies.append(
                Anomaly(
                    severity=severity,
                    category="missing_tag",
                    title="Assets without TAG assignment",
                    description=(
                        f"{len(no_tag)} assets ({pct:.1f}%) have no TAG. "
                        f"This indicates devices not processed by synchronization."
                    ),
                    affected_assets=no_tag["hardware_id"].tolist()[:15],
                    suggestion=(
                        "Run TAG synchronization to resolve. "
                        "If they persist, verify that inventories appear in AR01."
                    ),
                )
            )

    def _detect_orphan_assets(self, df: pd.DataFrame) -> None:
        """Detect assets with no building, user, or meaningful data."""
        orphans = df[
            (df["edificio"].isna() | (df["edificio"].str.strip() == ""))
            & (df["usuario"].isna() | (df["usuario"].str.strip() == ""))
            & (df["tag"].isna() | (df["tag"].str.strip() == ""))
        ]

        if len(orphans) > 0:
            self.result.anomalies.append(
                Anomaly(
                    severity="warning",
                    category="orphan",
                    title="Orphan assets",
                    description=(
                        f"{len(orphans)} assets without building, user, or TAG. "
                        f"Possibly disconnected or misconfigured devices."
                    ),
                    affected_assets=orphans["hardware_id"].tolist()[:15],
                    suggestion=(
                        "Review these devices in OCS Inventory. They may be "
                        "temporary workstations, misconfigured VMs, or retired equipment."
                    ),
                )
            )

    def _detect_tag_pattern_anomalies(self, df: pd.DataFrame) -> None:
        """Detect TAGs that don't follow the expected Edificio-Local format."""
        tagged = df[df["tag"].notna() & (df["tag"].str.strip() != "")]
        if tagged.empty:
            return

        # Expected pattern: "EDIF-1234" or similar
        valid = tagged["tag"].str.match(self.TAG_PATTERN_REGEX, na=False)
        invalid_tags = tagged[~valid]

        if len(invalid_tags) > 0 and len(invalid_tags) < len(tagged):
            pct = len(invalid_tags) / len(tagged) * 100
            tag_samples = invalid_tags["tag"].unique()[:10].tolist()
            self.result.anomalies.append(
                Anomaly(
                    severity="info",
                    category="pattern",
                    title="Non-standard TAG format",
                    description=(
                        f"{len(invalid_tags)} TAGs ({pct:.1f}%) do not follow the "
                        f"expected Building-Office pattern. Examples: {tag_samples}"
                    ),
                    affected_assets=invalid_tags["hardware_id"].tolist()[:10],
                    suggestion=(
                        "TAGs should follow the 'BLDG-NNNN' format. "
                        "Verify the locations classifier."
                    ),
                )
            )

    def _detect_building_outliers(self, df: pd.DataFrame) -> None:
        """
        Use z-score analysis to find buildings with unusual asset counts.
        Buildings with counts > 2 std devs from mean are flagged.
        """
        tagged = df[df["tag"].notna() & (df["tag"].str.strip() != "")]
        if len(tagged) < 5:
            return

        buildings = tagged["tag"].apply(
            lambda x: x.split("-")[0] if "-" in str(x) else str(x)
        )
        counts = buildings.value_counts()

        if len(counts) < 3:
            return

        mean = counts.mean()
        std = counts.std()

        if std == 0:
            return

        outliers = []
        for building, count in counts.items():
            z_score = (count - mean) / std
            if abs(z_score) > 2.0:
                direction = "high concentration" if z_score > 0 else "very few assets"
                outliers.append(f"{building}: {count} assets ({direction})")

        if outliers:
            self.result.anomalies.append(
                Anomaly(
                    severity="info",
                    category="pattern",
                    title="Unusual distribution by building",
                    description=(
                        f"{len(outliers)} buildings detected with statistically "
                        f"unusual asset counts (|z| > 2.0)."
                    ),
                    affected_assets=outliers,
                    suggestion=(
                        "May indicate concentration from recent migration "
                        "or assets pending redistribution."
                    ),
                )
            )

    # ------------------------------------------------------------------
    # Data Quality Scoring
    # ------------------------------------------------------------------
    def _compute_data_quality(self, df: pd.DataFrame) -> None:
        """Compute a composite data quality score (0-100)."""
        total = len(df)
        if total == 0:
            self.result.data_quality = DataQualityReport(
                score=0, grade="F",
                completeness=0, consistency=0, uniqueness=0, validity=0,
            )
            return

        issues = []

        # Completeness: % of key fields that are non-null/non-empty
        key_fields = ["tag", "edificio", "noinventario", "usuario", "fields_3"]
        filled = sum(
            df[col].notna().sum() + (df[col].astype(str).str.strip() != "").sum()
            for col in key_fields if col in df.columns
        )
        completeness = (filled / (total * len(key_fields) * 2)) * 100
        if completeness < 70:
            issues.append(f"Low completeness: {completeness:.0f}% of key fields filled")

        # Consistency: % of TAGs following the expected pattern
        tagged = df[df["tag"].notna() & (df["tag"].str.strip() != "")]
        if len(tagged) > 0:
            valid_format = tagged["tag"].str.match(
                self.TAG_PATTERN_REGEX, na=False
            ).sum()
            consistency = (valid_format / len(tagged)) * 100
        else:
            consistency = 0.0
        if consistency < 80:
            issues.append(f"TAG format consistency: {consistency:.0f}%")

        # Uniqueness: % of unique inventory numbers (excluding MV and empty)
        inv = df["fields_3"].dropna()
        inv = inv[(inv != "MV") & (inv.str.strip() != "")]
        if len(inv) > 0:
            uniqueness = (inv.nunique() / len(inv)) * 100
        else:
            uniqueness = 100.0
        if uniqueness < 95:
            issues.append(f"Inventory uniqueness: {uniqueness:.0f}%")

        # Validity: % of assets that have either TAG or are classified as MV
        classified = (
            df["tag"].notna() & (df["tag"].str.strip() != "")
        ) | (df["fields_3"] == "MV")
        validity = (classified.sum() / total) * 100
        if validity < 80:
            issues.append(f"Validity (classified assets): {validity:.0f}%")

        # Composite score (weighted average)
        score = (
            completeness * 0.25
            + consistency * 0.25
            + uniqueness * 0.25
            + validity * 0.25
        )

        self.result.data_quality = DataQualityReport(
            score=round(score, 1),
            grade=DataQualityReport.compute_grade(score),
            completeness=round(completeness, 1),
            consistency=round(consistency, 1),
            uniqueness=round(uniqueness, 1),
            validity=round(validity, 1),
            issues=issues,
        )

    # ------------------------------------------------------------------
    # Distribution Analysis
    # ------------------------------------------------------------------
    def _analyze_distributions(self, df: pd.DataFrame) -> None:
        """Analyze asset distribution patterns."""
        total = len(df)

        # TAG status distribution
        with_tag = df["tag"].notna() & (df["tag"].str.strip() != "")
        is_mv = df["fields_3"] == "MV"
        is_empty = df["fields_3"].isna() | (df["fields_3"].str.strip() == "")

        self.result.distribution["tag_status"] = {
            "With TAG": int(with_tag.sum()),
            "Without TAG": int((~with_tag & ~is_mv).sum()),
            "Virtual Machines": int(is_mv.sum()),
        }

        # Building distribution (top 10)
        tagged = df[with_tag].copy()
        if not tagged.empty:
            tagged["building"] = tagged["tag"].apply(
                lambda x: x.split("-")[0] if "-" in str(x) else str(x)
            )
            building_dist = (
                tagged["building"]
                .value_counts()
                .head(10)
                .to_dict()
            )
            self.result.distribution["buildings"] = building_dist

        # User distribution (top 10)
        user_dist = (
            df["usuario"]
            .dropna()
            .loc[lambda s: s.str.strip() != ""]
            .value_counts()
            .head(10)
            .to_dict()
        )
        self.result.distribution["users"] = user_dist

        # Asset category breakdown
        self.result.distribution["categories"] = {
            "Physical with inventory": int(
                (~is_mv & ~is_empty & df["fields_3"].notna()).sum()
            ),
            "Virtual Machines": int(is_mv.sum()),
            "No inventory number": int(is_empty.sum()),
        }

        # Entropy of building distribution (measure of balance)
        if "buildings" in self.result.distribution:
            counts = list(self.result.distribution["buildings"].values())
            total_b = sum(counts)
            if total_b > 0:
                probs = [c / total_b for c in counts]
                entropy = -sum(p * math.log2(p) for p in probs if p > 0)
                max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1
                balance = (entropy / max_entropy * 100) if max_entropy else 100
                self.result.distribution["building_balance"] = round(balance, 1)

    # ------------------------------------------------------------------
    # Predictions & Recommendations
    # ------------------------------------------------------------------
    def _generate_predictions(self, df: pd.DataFrame) -> None:
        """Generate predictive insights and recommendations."""
        total = len(df)
        if total == 0:
            return

        with_tag = (df["tag"].notna() & (df["tag"].str.strip() != "")).sum()
        mv_count = (df["fields_3"] == "MV").sum()
        tag_pct = with_tag / total * 100

        # Estimated sync needed
        without_tag = total - with_tag - mv_count
        avg_sync_rate = 0.85  # Estimated 85% success rate per sync
        estimated_resolved = int(without_tag * avg_sync_rate)

        self.result.predictions["sync_estimate"] = {
            "pending_assets": without_tag,
            "estimated_resolved": estimated_resolved,
            "estimated_remaining": without_tag - estimated_resolved,
            "success_rate": avg_sync_rate * 100,
        }

        # Coverage projection
        if tag_pct < 100:
            target_95 = max(0, int(total * 0.95) - with_tag - mv_count)
            self.result.predictions["coverage"] = {
                "current_pct": round(tag_pct, 1),
                "target_pct": 95.0,
                "assets_needed": target_95,
                "message": (
                    f"{target_95} assets needed to reach 95% TAG coverage."
                    if target_95 > 0
                    else "Already exceeding 95% coverage."
                ),
            }

        # Recommendations
        recommendations = []
        if without_tag > 0:
            recommendations.append({
                "priority": "high",
                "action": "Run TAG synchronization",
                "impact": f"Could resolve ~{estimated_resolved} pending assets",
                "icon": "bi-arrow-repeat",
            })

        dupe_anomalies = [
            a for a in self.result.anomalies if a.category == "duplicate"
        ]
        if dupe_anomalies:
            recommendations.append({
                "priority": "high",
                "action": "Resolve duplicate inventories",
                "impact": "Eliminates TAG assignment conflicts",
                "icon": "bi-exclamation-triangle",
            })

        orphan_anomalies = [
            a for a in self.result.anomalies if a.category == "orphan"
        ]
        if orphan_anomalies:
            recommendations.append({
                "priority": "medium",
                "action": "Audit orphan assets",
                "impact": "Cleans invalid records from the database",
                "icon": "bi-search",
            })

        if self.result.data_quality and self.result.data_quality.completeness < 70:
            recommendations.append({
                "priority": "medium",
                "action": "Improve data completeness",
                "impact": "More reliable information for reports and audits",
                "icon": "bi-clipboard-data",
            })

        balance = self.result.distribution.get("building_balance", 100)
        if balance < 50:
            recommendations.append({
                "priority": "low",
                "action": "Review asset distribution by building",
                "impact": "More balanced IT resource distribution",
                "icon": "bi-building",
            })

        self.result.predictions["recommendations"] = recommendations

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def _build_summary(self, df: pd.DataFrame) -> None:
        """Build a top-level summary for the analytics dashboard."""
        total = len(df)
        critical = sum(1 for a in self.result.anomalies if a.severity == "critical")
        warnings = sum(1 for a in self.result.anomalies if a.severity == "warning")

        self.result.summary = {
            "total_assets": total,
            "total_anomalies": len(self.result.anomalies),
            "critical_anomalies": critical,
            "warning_anomalies": warnings,
            "quality_score": self.result.data_quality.score if self.result.data_quality else 0,
            "quality_grade": self.result.data_quality.grade if self.result.data_quality else "F",
            "generated_at": self.result.generated_at,
        }
