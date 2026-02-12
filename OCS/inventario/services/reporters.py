"""
reporters.py — Report generation for ETECSA Asset Sync.

Generates multi-sheet Excel reports from sync results.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .processors import SyncResult

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates Excel reports from TAG synchronization results."""

    def __init__(self, output_path: str = "Reports.xlsx"):
        self.output_path = output_path

    def generate(self, result: SyncResult) -> Path:
        """
        Generate a multi-sheet Excel report from sync results.

        Args:
            result: The SyncResult from a TagSyncProcessor run.

        Returns:
            Path to the generated Excel file.
        """
        cols = result.column_names

        df_empty = pd.DataFrame(result.empty_inventories, columns=cols)
        df_vm = pd.DataFrame(result.vm_inventories, columns=cols)
        df_duplicates = pd.DataFrame(result.duplicate_inventories, columns=cols)
        df_not_in_ar01 = pd.DataFrame(result.db_not_in_ar01, columns=cols)

        df_locations_not_classified = pd.DataFrame(
            result.locations_not_in_classifier,
            columns=["Inventory", "Location"],
        )

        df_ar01_not_in_db = pd.DataFrame(
            {
                "AR01 Inventory not in DB": result.ar01_not_in_db,
                "Corresponding Location": result.corresponding_locations,
            }
        )

        sheets = [
            ("Empty_Inventories", df_empty),
            ("VM_Inventories", df_vm),
            ("Locations_Not_In_Classifier", df_locations_not_classified),
            ("Duplicate_Inventories", df_duplicates),
            ("DB_Not_In_AR01", df_not_in_ar01),
            ("AR01_Not_In_DB", df_ar01_not_in_db),
        ]

        with pd.ExcelWriter(self.output_path, engine="openpyxl") as writer:
            for sheet_name, df in sheets:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                logger.info(
                    f"  Sheet '{sheet_name}': {len(df)} records"
                )
            self._auto_fit_columns(writer)

        output = Path(self.output_path)
        logger.info(f"Report generated: {output.absolute()}")
        return output

    @staticmethod
    def _auto_fit_columns(writer: pd.ExcelWriter) -> None:
        """Auto-fit column widths in all sheets."""
        for sheet in writer.sheets.values():
            for col in sheet.columns:
                max_len = max(
                    (len(str(cell.value)) for cell in col if cell.value),
                    default=0,
                )
                adjusted = (max_len + 2) * 1.2
                sheet.column_dimensions[col[0].column_letter].width = adjusted
