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

    def __init__(self, output_path: str = "Reportes.xlsx"):
        self.output_path = output_path

    def generate(self, result: SyncResult) -> Path:
        """
        Generate a multi-sheet Excel report from sync results.

        Args:
            result: The SyncResult from a TagSyncProcessor run.

        Returns:
            Path to the generated Excel file.
        """
        cols = result.nombres_columnas

        df_vacios = pd.DataFrame(result.inventarios_vacios, columns=cols)
        df_mv = pd.DataFrame(result.inventarios_mv, columns=cols)
        df_duplicados = pd.DataFrame(result.inventarios_duplicados, columns=cols)
        df_no_ar01 = pd.DataFrame(result.inv_bd_no_estan_AR01, columns=cols)

        df_locales_no_clasif = pd.DataFrame(
            result.locales_no_estan_clasificador,
            columns=["Inventario", "Local"],
        )

        df_ar01_no_bd = pd.DataFrame(
            {
                "Inventario en AR01 no en DB": result.inventarios_AR01_no_en_BD,
                "Local Correspondiente": result.locales_correspondientes,
            }
        )

        sheets = [
            ("Inventarios_Vacíos", df_vacios),
            ("Inventarios_MV", df_mv),
            ("Locales_no_Clasificador", df_locales_no_clasif),
            ("Inventarios_Duplicados", df_duplicados),
            ("Inv_BD_no_en_AR01", df_no_ar01),
            ("Inv_AR01_no_en_DB", df_ar01_no_bd),
        ]

        with pd.ExcelWriter(self.output_path, engine="openpyxl") as writer:
            for sheet_name, df in sheets:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                logger.info(
                    f"  Hoja '{sheet_name}': {len(df)} registros"
                )
            self._auto_fit_columns(writer)

        output = Path(self.output_path)
        logger.info(f"Reporte generado: {output.absolute()}")
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
