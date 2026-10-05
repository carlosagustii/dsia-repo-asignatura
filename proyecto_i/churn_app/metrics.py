"""KPIs de un negocio de suscripción: churn, MRR y cohortes de antigüedad.

Glosario rápido (vocabulario estándar en SaaS / telco):

* **Churn rate**: % de clientes que se han dado de baja.
* **MRR** (*Monthly Recurring Revenue*): ingresos mensuales recurrentes de los
  clientes que siguen activos.
* **MRR perdido**: cuota mensual que se ha ido con los clientes que abandonan.
* **ARPU** (*Average Revenue Per User*): cuota mensual media por cliente.
"""

from __future__ import annotations

import pandas as pd

# Cohortes de antigüedad en meses: (límite inferior exclusivo, superior inclusivo].
TENURE_BINS: tuple[int, ...] = (-1, 12, 24, 48, 10_000)
TENURE_LABELS: tuple[str, ...] = ("0-12 meses", "13-24 meses", "25-48 meses", "49+ meses")

SEGMENT_COLUMNS: tuple[str, ...] = (
    "Contract",
    "InternetService",
    "PaymentMethod",
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "PaperlessBilling",
    "TechSupport",
    "OnlineSecurity",
)


def _pct(value: float) -> float:
    return round(float(value) * 100, 2)


class ChurnMetrics:
    """Métricas sobre el DataFrame limpio que devuelve ``CustomerValidator``."""

    def __init__(self, customers: pd.DataFrame) -> None:
        self._customers = customers

    @property
    def n_customers(self) -> int:
        return len(self._customers)

    def churn_rate(self) -> float:
        """% de clientes que han abandonado (0 si no hay clientes)."""
        if self._customers.empty:
            return 0.0
        return _pct(self._customers["Churn"].mean())

    def churn_rate_by(self, column: str) -> dict[str, float]:
        """% de churn por segmento, de más a menos arriesgado."""
        if column not in self._customers.columns:
            raise KeyError(f"Columna desconocida para segmentar: {column}")
        rates = self._customers.groupby(column)["Churn"].mean().sort_values(ascending=False)
        return {str(segment): _pct(rate) for segment, rate in rates.items()}

    def churn_by_tenure_cohort(self) -> dict[str, float]:
        """% de churn por antigüedad: muestra si el riesgo se concentra al principio."""
        cohorts = pd.cut(self._customers["tenure"], bins=TENURE_BINS, labels=TENURE_LABELS)
        rates = self._customers.groupby(cohorts, observed=False)["Churn"].mean()
        return {str(label): _pct(rate) if pd.notna(rate) else 0.0 for label, rate in rates.items()}

    def mrr(self) -> float:
        """Ingresos mensuales recurrentes de los clientes activos."""
        active = self._customers.loc[~self._customers["Churn"], "MonthlyCharges"]
        return round(float(active.sum()), 2)

    def lost_mrr(self) -> float:
        """Cuota mensual que se ha perdido con los clientes que abandonan."""
        churned = self._customers.loc[self._customers["Churn"], "MonthlyCharges"]
        return round(float(churned.sum()), 2)

    def lost_mrr_pct(self) -> float:
        """% del MRR bruto (activos + perdidos) que se ha ido con el churn."""
        gross = self.mrr() + self.lost_mrr()
        return _pct(self.lost_mrr() / gross) if gross else 0.0

    def arpu_by_churn(self) -> dict[str, float]:
        """Cuota media de quien se queda vs. quien se va."""
        arpu = self._customers.groupby("Churn")["MonthlyCharges"].mean()
        labels = {False: "activos", True: "bajas"}
        return {labels[bool(key)]: round(float(value), 2) for key, value in arpu.items()}

    def summary(self, segment: str = "Contract") -> dict[str, object]:
        return {
            "clientes_validos": self.n_customers,
            "churn_pct": self.churn_rate(),
            "mrr_activo": self.mrr(),
            "mrr_perdido": self.lost_mrr(),
            "mrr_perdido_pct": self.lost_mrr_pct(),
            "arpu": self.arpu_by_churn(),
            "segmento": segment,
            "churn_pct_por_segmento": self.churn_rate_by(segment),
            "churn_pct_por_antiguedad": self.churn_by_tenure_cohort(),
        }
