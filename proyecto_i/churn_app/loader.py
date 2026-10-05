"""Carga del dataset de clientes (CSV) con comprobación de esquema."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

import pandas as pd

from churn_app.exceptions import DataLoadError, SchemaError

logger = logging.getLogger(__name__)

SOURCE_URL = (
    "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/"
    "master/data/Telco-Customer-Churn.csv"
)

YES_NO_COLUMNS: tuple[str, ...] = ("Partner", "Dependents", "PhoneService", "PaperlessBilling")
INTERNET_ADDON_COLUMNS: tuple[str, ...] = (
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
)

REQUIRED_COLUMNS: tuple[str, ...] = (
    "customerID",
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    *INTERNET_ADDON_COLUMNS,
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
    "Churn",
)


class CustomerRepository(Protocol):
    """Cualquier origen capaz de devolver la tabla de clientes."""

    def load(self) -> pd.DataFrame: ...


class CsvCustomerRepository:
    """Lee clientes de un CSV, en crudo (todo texto) y con esquema verificado."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> pd.DataFrame:
        if not self._path.is_file():
            raise DataLoadError(f"No existe el fichero de clientes: {self._path}")
        try:
            frame = pd.read_csv(self._path, dtype=str, keep_default_na=False)
        except pd.errors.EmptyDataError as exc:
            raise DataLoadError(f"El fichero está vacío: {self._path}") from exc
        except (pd.errors.ParserError, UnicodeDecodeError) as exc:
            raise DataLoadError(f"No se pudo parsear {self._path}: {exc}") from exc

        frame.columns = [column.strip() for column in frame.columns]
        missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
        if missing:
            raise SchemaError(f"Faltan columnas obligatorias: {', '.join(missing)}")

        logger.info("Cargados %d clientes desde %s", len(frame), self._path)
        return frame


def load_customers(path: str | Path) -> pd.DataFrame:
    """Atajo funcional: ``load_customers("data/telco_churn.csv")``."""
    return CsvCustomerRepository(path).load()
