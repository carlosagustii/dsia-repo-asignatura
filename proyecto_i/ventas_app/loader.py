"""Carga de datos de ventas desde CSV.

Se expone un ``Protocol`` (``SalesRepository``) para que el resto del pipeline
no dependa de un formato concreto (DIP): mañana puede ser JSON, una base de
datos o una API sin tocar ``validator`` ni ``metrics``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

import pandas as pd

from ventas_app.exceptions import DataLoadError, SchemaError

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS: tuple[str, ...] = (
    "fecha",
    "region",
    "producto",
    "unidades",
    "precio_unitario",
    "cliente_id",
)


class SalesRepository(Protocol):
    """Cualquier origen capaz de devolver las ventas como DataFrame."""

    def load(self) -> pd.DataFrame: ...


class CsvSalesRepository:
    """Lee ventas de un CSV y comprueba que trae las columnas obligatorias."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> pd.DataFrame:
        if not self._path.is_file():
            raise DataLoadError(f"No existe el fichero de ventas: {self._path}")
        try:
            # dtype=str: se carga "en crudo"; convertir tipos es tarea del validador.
            frame = pd.read_csv(self._path, dtype=str, keep_default_na=False)
        except pd.errors.EmptyDataError as exc:
            raise DataLoadError(f"El fichero está vacío: {self._path}") from exc
        except (pd.errors.ParserError, UnicodeDecodeError) as exc:
            raise DataLoadError(f"No se pudo parsear {self._path}: {exc}") from exc

        frame.columns = [column.strip() for column in frame.columns]
        missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
        if missing:
            raise SchemaError(f"Faltan columnas obligatorias: {', '.join(missing)}")

        logger.info("Cargadas %d filas desde %s", len(frame), self._path)
        return frame


def load_sales(path: str | Path) -> pd.DataFrame:
    """Atajo funcional: ``load_sales("data/ventas.csv")``."""
    return CsvSalesRepository(path).load()
