"""
processors.py — Core sync engine for ETECSA Asset Sync.

Handles the cross-referencing logic between the OCS database,
AR01 Finance report, and HR Locations Classifier.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import mysql.connector  # type: ignore
import pandas as pd

from .data_sources import ExcelDataSources

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Container for the results of a TAG synchronization run."""

    tags_updated: int = 0
    total_processed: int = 0
    inventarios_vacios: list = field(default_factory=list)
    inventarios_mv: list = field(default_factory=list)
    inventarios_duplicados: list = field(default_factory=list)
    inv_bd_no_estan_AR01: list = field(default_factory=list)
    locales_no_estan_clasificador: list = field(default_factory=list)
    inventarios_AR01_no_en_BD: list = field(default_factory=list)
    locales_correspondientes: list = field(default_factory=list)
    nombres_columnas: list = field(default_factory=list)

    @property
    def summary(self) -> dict[str, int]:
        """Return a summary dict of counts for the dashboard."""
        return {
            "total_processed": self.total_processed,
            "tags_updated": self.tags_updated,
            "empty_inventory": len(self.inventarios_vacios),
            "virtual_machines": len(self.inventarios_mv),
            "duplicates": len(self.inventarios_duplicados),
            "not_in_ar01": len(self.inv_bd_no_estan_AR01),
            "not_in_classifier": len(self.locales_no_estan_clasificador),
            "ar01_not_in_db": len(self.inventarios_AR01_no_en_BD),
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
        nombre_tabla: str = "accountinfo",
        nombre_columna: str = "fields_3",
    ):
        self.data_sources = data_sources
        self.db_config = db_config
        self.nombre_tabla = nombre_tabla
        self.nombre_columna = nombre_columna

    def execute(self) -> SyncResult:
        """
        Run the full TAG synchronization process.

        Returns:
            SyncResult with all categorized data and update counts.
        """
        result = SyncResult()
        connection = None
        cursor = None

        try:
            logger.info("Conectando a la base de datos MySQL...")
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()

            # Fetch all rows
            cursor.execute(f"SELECT * FROM {self.nombre_tabla}")
            filas_bd = cursor.fetchall()
            result.nombres_columnas = [desc[0] for desc in cursor.description]

            col_idx = result.nombres_columnas.index(self.nombre_columna)
            hw_idx = result.nombres_columnas.index("HARDWARE_ID")

            inventario_vistos: dict[str, list] = {}
            inventarios_en_bd: list[str] = []
            inventarios_AR01 = self.data_sources.inventarios_AR01_limpios

            logger.info(f"Procesando {len(filas_bd)} registros...")

            for index, fila in enumerate(filas_bd, start=1):
                numero_inventario = fila[col_idx]
                result.total_processed += 1

                if numero_inventario is None:
                    result.inventarios_vacios.append(fila)
                    continue

                if numero_inventario == "MV":
                    result.inventarios_mv.append(fila)
                    continue

                numero_inventario = str(numero_inventario).strip()
                inventarios_en_bd.append(numero_inventario)
                inventario_vistos.setdefault(numero_inventario, []).append(
                    (fila, fila[hw_idx])
                )

                if numero_inventario not in inventarios_AR01:
                    result.inv_bd_no_estan_AR01.append(fila)

                # Cross-reference with Excel sources
                tag_value = self._resolve_tag(numero_inventario)
                if tag_value:
                    self._update_tag(cursor, connection, numero_inventario, tag_value)
                    result.tags_updated += 1
                elif tag_value is None:
                    local = self.data_sources.buscar_inventario_y_local(numero_inventario)
                    if local:
                        result.locales_no_estan_clasificador.append(
                            (numero_inventario, local)
                        )

            # Detect duplicates
            for inv_num, valores in inventario_vistos.items():
                if len(valores) > 1:
                    sorted_vals = sorted(
                        valores, key=lambda x: x[1], reverse=True
                    )
                    for fila, _ in sorted_vals:
                        fila_dict = dict(zip(result.nombres_columnas, fila))
                        tag = self._resolve_tag(str(fila[col_idx]).strip())
                        if tag:
                            fila_dict["TAG"] = tag
                        result.inventarios_duplicados.append(fila_dict)

            # Find AR01 assets not in database
            result.inventarios_AR01_no_en_BD = [
                inv for inv in inventarios_AR01 if inv not in inventarios_en_bd
            ]
            result.locales_correspondientes = [
                self.data_sources.buscar_inventario_y_local(inv)
                for inv in result.inventarios_AR01_no_en_BD
            ]

            logger.info(
                f"Sincronización completada: {result.tags_updated} TAGs actualizados "
                f"de {result.total_processed} registros procesados."
            )

        except mysql.connector.Error as err:
            logger.error(f"Error de base de datos: {err}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

        return result

    def _resolve_tag(self, numero_inventario: str) -> Optional[str]:
        """Resolve the TAG value for a given inventory number."""
        local = self.data_sources.buscar_inventario_y_local(numero_inventario)
        if local:
            valores = self.data_sources.buscar_valores_en_clasificador(local)
            if valores:
                descrip, edificio = valores
                return f"{edificio}-{descrip}"
        return None

    def _update_tag(
        self,
        cursor: Any,
        connection: Any,
        numero_inventario: str,
        tag_value: str,
    ) -> None:
        """Update the TAG field in the database."""
        query = f"""
            UPDATE {self.nombre_tabla}
            SET `TAG` = %s
            WHERE TRIM(`{self.nombre_columna}`) = %s
        """
        cursor.execute(query, (tag_value, numero_inventario))
        connection.commit()
        logger.info(f"TAG actualizado: {numero_inventario} → {tag_value}")
