"""Reglas de calidad para clientes de una operadora con suscripción mensual.

Cada regla marca las filas que la **incumplen**. Las reglas combinan:

* **tipos y rangos** (antigüedad entera 0–120 meses, cuota mensual 0–500 €),
* **dominios cerrados** (tipo de contrato, método de pago, Yes/No…),
* **unicidad** (``customerID`` no repetido),
* **coherencia de negocio** (sin internet ⇒ sin servicios de internet;
  ``TotalCharges`` ≈ ``tenure × MonthlyCharges``).

Normalización documentada: los clientes con ``tenure == 0`` (recién dados de
alta) todavía no han recibido factura y traen ``TotalCharges`` vacío. No es un
error: se imputa ``0.0`` y se contabiliza en ``ValidationResult.n_imputed``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from churn_app.exceptions import ValidationError
from churn_app.loader import INTERNET_ADDON_COLUMNS, REQUIRED_COLUMNS, YES_NO_COLUMNS

Rule = Callable[[pd.DataFrame], pd.Series]

REASON_COLUMN = "motivo"
CUSTOMER_ID_PATTERN = r"^\d{4}-[A-Z]{5}$"
MAX_TENURE_MONTHS = 120
MAX_MONTHLY_CHARGE = 500.0
# Tolerancia de TotalCharges frente a tenure * MonthlyCharges (subidas/bajadas de tarifa).
TOTAL_CHARGES_RATIO = (0.5, 2.0)

DOMAINS: dict[str, frozenset[str]] = {
    "gender": frozenset({"Female", "Male"}),
    "SeniorCitizen": frozenset({"0", "1"}),
    "MultipleLines": frozenset({"Yes", "No", "No phone service"}),
    "InternetService": frozenset({"DSL", "Fiber optic", "No"}),
    "Contract": frozenset({"Month-to-month", "One year", "Two year"}),
    "PaymentMethod": frozenset(
        {
            "Electronic check",
            "Mailed check",
            "Bank transfer (automatic)",
            "Credit card (automatic)",
        }
    ),
    "Churn": frozenset({"Yes", "No"}),
    **{column: frozenset({"Yes", "No"}) for column in YES_NO_COLUMNS},
    **{column: frozenset({"Yes", "No", "No internet service"}) for column in INTERNET_ADDON_COLUMNS},
}


def _text(frame: pd.DataFrame, column: str) -> pd.Series:
    return frame[column].astype(str).str.strip()


def _number(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def bad_customer_id(frame: pd.DataFrame) -> pd.Series:
    return ~_text(frame, "customerID").str.fullmatch(CUSTOMER_ID_PATTERN)


def duplicated_customer_id(frame: pd.DataFrame) -> pd.Series:
    return _text(frame, "customerID").duplicated(keep="first")


def out_of_domain(frame: pd.DataFrame) -> pd.Series:
    failed = pd.Series(False, index=frame.index)
    for column, allowed in DOMAINS.items():
        failed |= ~_text(frame, column).isin(allowed)
    return failed


def bad_tenure(frame: pd.DataFrame) -> pd.Series:
    tenure = _number(frame, "tenure")
    return ~tenure.between(0, MAX_TENURE_MONTHS) | (tenure % 1 != 0)


def bad_monthly_charges(frame: pd.DataFrame) -> pd.Series:
    charges = _number(frame, "MonthlyCharges")
    return ~((charges > 0) & (charges <= MAX_MONTHLY_CHARGE))


def bad_total_charges(frame: pd.DataFrame) -> pd.Series:
    """TotalCharges debe ser numérico y >= 0, salvo vacío en clientes nuevos (tenure 0)."""
    raw = _text(frame, "TotalCharges")
    total = _number(frame, "TotalCharges")
    new_customer_blank = (raw == "") & (_number(frame, "tenure") == 0)
    return ~((total >= 0) | new_customer_blank)


def inconsistent_total_charges(frame: pd.DataFrame) -> pd.Series:
    tenure = _number(frame, "tenure")
    expected = tenure * _number(frame, "MonthlyCharges")
    ratio = _number(frame, "TotalCharges") / expected
    low, high = TOTAL_CHARGES_RATIO
    # Solo aplica cuando hay datos para comparar; los demás casos ya los cubren otras reglas.
    comparable = (tenure > 0) & ratio.notna()
    return comparable & ~ratio.between(low, high)


def inconsistent_services(frame: pd.DataFrame) -> pd.Series:
    """Sin internet ⇒ addons 'No internet service'; sin teléfono ⇒ 'No phone service'."""
    no_internet = _text(frame, "InternetService") == "No"
    addons_say_no_internet = pd.concat(
        [_text(frame, column) == "No internet service" for column in INTERNET_ADDON_COLUMNS],
        axis=1,
    )
    internet_mismatch = (no_internet & ~addons_say_no_internet.all(axis=1)) | (
        ~no_internet & addons_say_no_internet.any(axis=1)
    )
    no_phone = _text(frame, "PhoneService") == "No"
    phone_mismatch = no_phone != (_text(frame, "MultipleLines") == "No phone service")
    return internet_mismatch | phone_mismatch


DEFAULT_RULES: dict[str, Rule] = {
    "customerID con formato inválido": bad_customer_id,
    "customerID duplicado": duplicated_customer_id,
    "valor fuera de dominio": out_of_domain,
    "tenure no entero o fuera de [0, 120]": bad_tenure,
    "MonthlyCharges fuera de (0, 500]": bad_monthly_charges,
    "TotalCharges no numérico o negativo": bad_total_charges,
    "TotalCharges incoherente con tenure × MonthlyCharges": inconsistent_total_charges,
    "servicios incoherentes": inconsistent_services,
}


@dataclass(frozen=True)
class ValidationResult:
    valid: pd.DataFrame
    invalid: pd.DataFrame
    n_imputed: int = 0

    @property
    def n_valid(self) -> int:
        return len(self.valid)

    @property
    def n_invalid(self) -> int:
        return len(self.invalid)


class CustomerValidator:
    """Aplica las reglas, devuelve clientes limpios (tipados) y rechazados (con motivo)."""

    def __init__(self, rules: dict[str, Rule] | None = None) -> None:
        self._rules = dict(DEFAULT_RULES if rules is None else rules)

    def validate(self, frame: pd.DataFrame) -> ValidationResult:
        missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
        if missing:
            raise ValidationError(f"No se puede validar; faltan columnas: {', '.join(missing)}")

        failures = pd.DataFrame(
            {name: rule(frame).fillna(True).astype(bool) for name, rule in self._rules.items()},
            index=frame.index,
        )
        is_invalid = failures.any(axis=1) if self._rules else pd.Series(False, index=frame.index)

        invalid = frame.loc[is_invalid].copy()
        invalid[REASON_COLUMN] = [
            "; ".join(failures.columns[row]) for row in failures.loc[is_invalid].to_numpy()
        ]

        valid, n_imputed = self._clean(frame.loc[~is_invalid])
        return ValidationResult(valid=valid, invalid=invalid, n_imputed=n_imputed)

    @staticmethod
    def _clean(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        clean = frame.apply(lambda column: column.astype(str).str.strip())
        total = pd.to_numeric(clean["TotalCharges"], errors="coerce")
        n_imputed = int(total.isna().sum())

        clean["TotalCharges"] = total.fillna(0.0).astype("float64")
        clean["MonthlyCharges"] = pd.to_numeric(clean["MonthlyCharges"]).astype("float64")
        clean["tenure"] = pd.to_numeric(clean["tenure"]).astype("int64")
        clean["SeniorCitizen"] = pd.to_numeric(clean["SeniorCitizen"]).astype("int64")
        clean["Churn"] = clean["Churn"] == "Yes"
        return clean.reset_index(drop=True), n_imputed
