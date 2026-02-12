"""
processors.py — Core sync engine for ETECSA Asset Sync.

Handles the cross-referencing logic between the OCS database,
AR01 Finance report, and HR Locations Classifier.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from django.db import connection as django_connection
import pandas as pd

from .data_sources import ExcelDataSources

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Container for the results of a TAG synchronization run."""

    tags_updated: int = 0
    total_processed: int = 0
    empty_inventories: list = field(default_factory=list)
    vm_inventories: list = field(default_factory=list)
    duplicate_inventories: list = field(default_factory=list)
    db_not_in_ar01: list = field(default_factory=list)
    locations_not_in_classifier: list = field(default_factory=list)
    ar01_not_in_db: list = field(default_factory=list)
    corresponding_locations: list = field(default_factory=list)
    column_names: list = field(default_factory=list)

    @property
    def summary(self) -> dict[str, int]:
        """Return a summary dict of counts for the dashboard."""
        return {
            "total_processed": self.total_processed,
            "tags_updated": self.tags_updated,
            "empty_inventory": len(self.empty_inventories),
            "virtual_machines": len(self.vm_inventories),
            "duplicates": len(self.duplicate_inventories),
            "not_in_ar01": len(self.db_not_in_ar01),
            "not_in_classifier": len(self.locations_not_in_classifier),
            "ar01_not_in_db": len(self.ar01_not_in_db),
        }


class TagSyncProcessor:
    """
    Orchestrates the TAG synchronization between OCS Inventory DB
    and Excel data sources (AR01 + Locations Classifier).
    """

    def __init__(
        self,
        data_sources: ExcelDataSources,
        db_config: dict[str, Any],
        table_name: str = "accountinfo",
        column_name: str = "fields_3",
    ):
        self.data_sources = data_sources
        self.db_config = db_config
        self.table_name = table_name
        self.column_name = column_name

    def execute(self) -> SyncResult:
        """
        Run the full TAG synchronization process using Django ORM.

        Returns:
            SyncResult with all categorized data and update counts.
        """
        result = SyncResult()

        try:
            logger.info("Running synchronization with Django ORM...")
            
            # Use Django's database connection (works with SQLite, MySQL, PostgreSQL, etc.)
            with django_connection.cursor() as cursor:
                # Fetch all rows
                cursor.execute(f"SELECT * FROM {self.table_name}")
                db_rows = cursor.fetchall()
                result.column_names = [desc[0] for desc in cursor.description]

                col_idx = result.column_names.index(self.column_name)
                
                # Try to find HARDWARE_ID column (case-insensitive)
                hw_idx = None
                for idx, col_name in enumerate(result.column_names):
                    if col_name.upper() == 'HARDWARE_ID':
                        hw_idx = idx
                        break
                
                if hw_idx is None:
                    logger.warning("Column HARDWARE_ID not found, using ID 0 as fallback")
                    hw_idx = 0

                seen_inventories: dict[str, list] = {}
                db_inventory_list: list[str] = []
                ar01_inventories = self.data_sources.clean_ar01_inventories

                logger.info(f"Processing {len(db_rows)} records...")

                for index, row in enumerate(db_rows, start=1):
                    inventory_number = row[col_idx]
                    result.total_processed += 1

                    if inventory_number is None:
                        result.empty_inventories.append(row)
                        continue

                    if inventory_number == "MV":
                        result.vm_inventories.append(row)
                        continue

                    inventory_number = str(inventory_number).strip()
                    db_inventory_list.append(inventory_number)
                    seen_inventories.setdefault(inventory_number, []).append(
                        (row, row[hw_idx])
                    )

                    if inventory_number not in ar01_inventories:
                        result.db_not_in_ar01.append(row)

                    # Cross-reference with Excel sources
                    tag_value = self._resolve_tag(inventory_number)
                    if tag_value:
                        self._update_tag(cursor, inventory_number, tag_value)
                        result.tags_updated += 1
                    elif tag_value is None:
                        local = self.data_sources.find_inventory_location(inventory_number)
                        if local:
                            result.locations_not_in_classifier.append(
                                (inventory_number, local)
                            )

                # Detect duplicates
                for inv_num, values in seen_inventories.items():
                    if len(values) > 1:
                        sorted_vals = sorted(
                            values, key=lambda x: x[1], reverse=True
                        )
                        for row, _ in sorted_vals:
                            row_dict = dict(zip(result.column_names, row))
                            tag = self._resolve_tag(str(row[col_idx]).strip())
                            if tag:
                                row_dict["TAG"] = tag
                            result.duplicate_inventories.append(row_dict)

                # Find AR01 assets not in database
                result.ar01_not_in_db = [
                    inv for inv in ar01_inventories if inv not in db_inventory_list
                ]
                result.corresponding_locations = [
                    self.data_sources.find_inventory_location(inv)
                    for inv in result.ar01_not_in_db
                ]

                logger.info(
                    f"Sync completed: {result.tags_updated} TAGs updated "
                    f"out of {result.total_processed} records processed."
                )

        except Exception as err:
            logger.error(f"Database error: {err}")
            raise

        return result

    def _resolve_tag(self, inventory_number: str) -> Optional[str]:
        """Resolve the TAG value for a given inventory number."""
        local = self.data_sources.find_inventory_location(inventory_number)
        if local:
            values = self.data_sources.find_classifier_values(local)
            if values:
                descrip, building = values
                return f"{building}-{descrip}"
        return None

    def _update_tag(
        self,
        cursor: Any,
        inventory_number: str,
        tag_value: str,
    ) -> None:
        """Update the TAG field in the database using Django connection."""
        query = f"""
            UPDATE {self.table_name}
            SET `TAG` = %s
            WHERE TRIM(`{self.column_name}`) = %s
        """
        cursor.execute(query, (tag_value, inventory_number))
        # Django's connection auto-commits in non-atomic contexts
        logger.info(f"TAG updated: {inventory_number} → {tag_value}")
