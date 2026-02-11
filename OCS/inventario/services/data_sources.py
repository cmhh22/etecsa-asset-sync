"""
data_sources.py — Data source loaders for the ETECSA Asset Sync engine.

Handles reading from Excel files (AR01 Finance report, HR Locations Classifier)
and the OCS Inventory MySQL database.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ExcelDataSources:
    """Loads and provides access to Excel-based data sources."""

    df_economia: pd.DataFrame = field(default_factory=pd.DataFrame)
    df_clasificador: pd.DataFrame = field(default_factory=pd.DataFrame)
    _inventarios_limpios: Optional[pd.Index] = field(default=None, repr=False)

    @classmethod
    def load(
        cls,
        archivo_economia: str,
        archivo_clasificador: str,
        skip_filas_economia: int = 8,
        columnas_economia: list[int] | None = None,
        columnas_clasificador: list[int] | None = None,
    ) -> "ExcelDataSources":
        """
        Load both Excel data sources from disk.

        Args:
            archivo_economia: Path to the AR01 Finance Excel file.
            archivo_clasificador: Path to the Locations Classifier Excel file.
            skip_filas_economia: Number of header rows to skip in AR01.
            columnas_economia: Column indices to read from AR01 [No_inventario, Local].
            columnas_clasificador: Column indices from classifier [ID_LOCAL, DESCRIP, EDIFICIO].
        """
        if columnas_economia is None:
            columnas_economia = [5, 8]
        if columnas_clasificador is None:
            columnas_clasificador = [4, 5, 6]

        logger.info(f"Cargando Excel de Economía: {archivo_economia}")
        df_eco = pd.read_excel(
            archivo_economia,
            skiprows=skip_filas_economia,
            usecols=columnas_economia,
        )

        logger.info(f"Cargando Clasificador de Locales: {archivo_clasificador}")
        df_clas = pd.read_excel(archivo_clasificador, usecols=columnas_clasificador)

        instance = cls(df_economia=df_eco, df_clasificador=df_clas)
        return instance

    @property
    def inventarios_AR01_limpios(self) -> list[str]:
        """Return cleaned inventory numbers from the AR01 report."""
        return self.df_economia.iloc[:, 0].astype(str).str.strip().values.tolist()

    def buscar_inventario_y_local(self, numero_inventario: str) -> Optional[str]:
        """
        Look up an inventory number in the AR01 and return its office code.

        Args:
            numero_inventario: The inventory number to search for.

        Returns:
            The office code (local) if found, None otherwise.
        """
        numero_inventario = numero_inventario.strip()
        col_inventario = self.df_economia.iloc[:, 0].astype(str).str.strip()

        if numero_inventario in col_inventario.values:
            idx = col_inventario[col_inventario == numero_inventario].index[0]
            local = self.df_economia.iloc[idx, 1]
            return local.strip() if isinstance(local, str) else local
        return None

    def buscar_valores_en_clasificador(
        self, local: str
    ) -> Optional[tuple[str, str]]:
        """
        Look up an office code in the Locations Classifier.

        Args:
            local: The office code to look up.

        Returns:
            Tuple of (description, building) if found, None otherwise.
        """
        local = str(local).strip()
        fila = self.df_clasificador[
            self.df_clasificador.iloc[:, 0].astype(str).str.strip() == local
        ]
        if not fila.empty:
            descrip_local = str(fila.iloc[0, 1]).strip().replace(" ", "_")
            edificio = str(fila.iloc[0, 2]).strip().replace(" ", "_")
            return descrip_local, edificio
        return None
