"""Validación de ventas: separa filas válidas e inválidas con su motivo.

Cada regla es una función pura ``DataFrame -> Series[bool]`` que marca las filas
que la **incumplen**. Añadir una regla nueva = añadir una entrada a
``DEFAULT_RULES`` (Open/Closed), sin tocar el resto del validador.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from ventas_app.exceptions import ValidationError
from ventas_app.loader import REQUIRED_COLUMNS

Rule = Callable[[pd.DataFrame], pd.Series]

REASON_COLUMN = "motivo"


def _as_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _is_blank(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip() == "")


def invalid_date(frame: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(frame["fecha"], format="%Y-%m-%d", errors="coerce").isna()


def missing_region(frame: pd.DataFrame) -> pd.Series:
    return _is_blank(frame["region"])


def missing_product(frame: pd.DataFrame) -> pd.Series:
    return _is_blank(frame["producto"])


def missing_customer(frame: pd.DataFrame) -> pd.Series:
    return _is_blank(frame["cliente_id"])


def non_positive_units(frame: pd.DataFrame) -> pd.Series:
    units = _as_number(frame["unidades"])
    # NaN > 0 es False, así que nulos y textos ("na") también caen aquí.
    return ~(units > 0)


def non_integer_units(frame: pd.DataFrame) -> pd.Series:
    units = _as_number(frame["unidades"])
    return (units > 0) & (units % 1 != 0)


def non_positive_price(frame: pd.DataFrame) -> pd.Series:
    return ~(_as_number(frame["precio_unitario"]) > 0)


DEFAULT_RULES: dict[str, Rule] = {
    "fecha inválida": invalid_date,
    "región vacía": missing_region,
    "producto vacío": missing_product,
    "cliente vacío": missing_customer,
    "unidades nulas, no numéricas o <= 0": non_positive_units,
    "unidades no enteras": non_integer_units,
    "precio nulo, no numérico o <= 0": non_positive_price,
}


@dataclass(frozen=True)
class ValidationResult:
    """Resultado de validar: filas limpias (tipadas) y filas rechazadas (con motivo)."""

    valid: pd.DataFrame
    invalid: pd.DataFrame

    @property
    def n_valid(self) -> int:
        return len(self.valid)

    @property
    def n_invalid(self) -> int:
        return len(self.invalid)

    @property
    def invalid_ratio(self) -> float:
        total = self.n_valid + self.n_invalid
        return self.n_invalid / total if total else 0.0


class SalesValidator:
    """Aplica un conjunto de reglas y devuelve un ``ValidationResult``."""

    def __init__(self, rules: dict[str, Rule] | None = None) -> None:
        self._rules = dict(DEFAULT_RULES if rules is None else rules)

    @property
    def rule_names(self) -> list[str]:
        return list(self._rules)

    def validate(self, frame: pd.DataFrame) -> ValidationResult:
        missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
        if missing:
            raise ValidationError(f"No se puede validar; faltan columnas: {', '.join(missing)}")

        # Una columna booleana por regla: True = la fila incumple esa regla.
        failures = pd.DataFrame(
            {name: rule(frame).fillna(True).astype(bool) for name, rule in self._rules.items()},
            index=frame.index,
        )
        is_invalid = failures.any(axis=1) if self._rules else pd.Series(False, index=frame.index)

        invalid = frame.loc[is_invalid].copy()
        invalid[REASON_COLUMN] = [
            "; ".join(failures.columns[row]) for row in failures.loc[is_invalid].to_numpy()
        ]

        return ValidationResult(valid=self._clean(frame.loc[~is_invalid]), invalid=invalid)

    @staticmethod
    def _clean(frame: pd.DataFrame) -> pd.DataFrame:
        """Convierte tipos de las filas ya validadas (seguro: todas pasan las reglas)."""
        clean = frame.copy()
        clean["fecha"] = pd.to_datetime(clean["fecha"], format="%Y-%m-%d")
        for column in ("region", "producto", "cliente_id"):
            clean[column] = clean[column].astype(str).str.strip()
        clean["unidades"] = _as_number(clean["unidades"]).astype("int64")
        clean["precio_unitario"] = _as_number(clean["precio_unitario"]).astype("float64")
        return clean.reset_index(drop=True)
