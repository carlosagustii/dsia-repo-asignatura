"""Métricas de negocio sobre ventas ya validadas."""

from __future__ import annotations

import pandas as pd

AMOUNT_COLUMN = "importe"


def with_amount(frame: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una copia con la columna ``importe = unidades * precio_unitario``."""
    result = frame.copy()
    result[AMOUNT_COLUMN] = result["unidades"] * result["precio_unitario"]
    return result


class SalesMetrics:
    """Agregaciones de negocio. Recibe el DataFrame *limpio* del validador."""

    def __init__(self, sales: pd.DataFrame) -> None:
        self._sales = with_amount(sales)

    @property
    def n_sales(self) -> int:
        return len(self._sales)

    def total_revenue(self) -> float:
        return round(float(self._sales[AMOUNT_COLUMN].sum()), 2)

    def total_units(self) -> int:
        return int(self._sales["unidades"].sum())

    def average_ticket(self) -> float:
        """Importe medio por venta (0 si no hay ventas)."""
        if self._sales.empty:
            return 0.0
        return round(float(self._sales[AMOUNT_COLUMN].mean()), 2)

    def revenue_by(self, column: str) -> dict[str, float]:
        """Importe total agrupado por ``column``, ordenado de mayor a menor."""
        if column not in self._sales.columns:
            raise KeyError(f"Columna desconocida para agrupar: {column}")
        totals = self._sales.groupby(column)[AMOUNT_COLUMN].sum().sort_values(ascending=False)
        return {str(key): round(float(value), 2) for key, value in totals.items()}

    def revenue_by_month(self) -> dict[str, float]:
        """Importe por mes (``YYYY-MM``) en orden cronológico."""
        months = self._sales["fecha"].dt.strftime("%Y-%m")
        totals = self._sales.groupby(months)[AMOUNT_COLUMN].sum().sort_index()
        return {str(key): round(float(value), 2) for key, value in totals.items()}

    def top_customers(self, n: int = 5) -> dict[str, float]:
        if n <= 0:
            raise ValueError("n debe ser positivo")
        return dict(list(self.revenue_by("cliente_id").items())[:n])

    def summary(self, top_n: int = 5) -> dict[str, object]:
        """Resumen serializable a JSON con todas las métricas."""
        return {
            "ventas_validas": self.n_sales,
            "importe_total": self.total_revenue(),
            "unidades_totales": self.total_units(),
            "ticket_medio": self.average_ticket(),
            "importe_por_region": self.revenue_by("region"),
            "importe_por_producto": self.revenue_by("producto"),
            "importe_por_mes": self.revenue_by_month(),
            "top_clientes": self.top_customers(top_n),
        }
