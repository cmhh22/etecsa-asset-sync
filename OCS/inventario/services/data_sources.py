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

    df_finance: pd.DataFrame = field(default_factory=pd.DataFrame)
    df_classifier: pd.DataFrame = field(default_factory=pd.DataFrame)
    _clean_inventories: Optional[pd.Index] = field(default=None, repr=False)

    @classmethod
    def load(
        cls,
        finance_file: str,
        classifier_file: str,
        skip_finance_rows: int = 8,
        finance_columns: list[int] | None = None,
        classifier_columns: list[int] | None = None,
    ) -> "ExcelDataSources":
        """
        Load both Excel data sources from disk.

        Args:
            finance_file: Path to the AR01 Finance Excel file.
            classifier_file: Path to the Locations Classifier Excel file.
            skip_finance_rows: Number of header rows to skip in AR01.
            finance_columns: Column indices to read from AR01 [Inventory_No, Location].
            classifier_columns: Column indices from classifier [LOCATION_ID, DESCRIPTION, BUILDING].
        """
        if finance_columns is None:
            finance_columns = [5, 8]
        if classifier_columns is None:
            classifier_columns = [4, 5, 6]

        logger.info(f"Loading Finance Excel: {finance_file}")
        df_fin = pd.read_excel(
            finance_file,
            skiprows=skip_finance_rows,
            usecols=finance_columns,
        )

        logger.info(f"Loading Locations Classifier: {classifier_file}")
        df_clas = pd.read_excel(classifier_file, usecols=classifier_columns)

        instance = cls(df_finance=df_fin, df_classifier=df_clas)
        return instance

    @property
    def clean_ar01_inventories(self) -> list[str]:
        """Return cleaned inventory numbers from the AR01 report."""
        return self.df_finance.iloc[:, 0].astype(str).str.strip().values.tolist()

    def find_inventory_location(self, inventory_number: str) -> Optional[str]:
        """
        Look up an inventory number in the AR01 and return its office code.

        Args:
            inventory_number: The inventory number to search for.

        Returns:
            The office code (location) if found, None otherwise.
        """
        inventory_number = str(inventory_number).strip()
        inventory_col = self.df_finance.iloc[:, 0].astype(str).str.strip()

        # Find matching rows
        mask = (inventory_col == inventory_number)
        if mask.any():
            idx = mask.idxmax()  # Get first matching index
            location = self.df_finance.iloc[idx, 1]
            return str(location).strip() if pd.notna(location) else None
        return None

    def find_classifier_values(
        self, location: str
    ) -> Optional[tuple[str, str]]:
        """
        Look up an office code in the Locations Classifier.

        Args:
            location: The office code to look up.

        Returns:
            Tuple of (description, building) if found, None otherwise.
        """
        location = str(location).strip()
        row = self.df_classifier[
            self.df_classifier.iloc[:, 0].astype(str).str.strip() == location
        ]
        if not row.empty:
            location_desc = str(row.iloc[0, 1]).strip().replace(" ", "_")
            building = str(row.iloc[0, 2]).strip().replace(" ", "_")
            return location_desc, building
        return None
