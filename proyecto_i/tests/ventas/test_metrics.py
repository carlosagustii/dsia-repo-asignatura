import pandas as pd
import pytest

from ventas_app.metrics import SalesMetrics


def test_importe_total_conocido(ventas_limpias):
    # 2*100 + 10*5 + 4*5 + 1*100 = 370
    assert SalesMetrics(ventas_limpias).total_revenue() == 370.0


def test_importe_por_region_ordenado(ventas_limpias):
    assert SalesMetrics(ventas_limpias).revenue_by("region") == {
        "Norte": 220.0,
        "Este": 100.0,
        "Sur": 50.0,
    }


def test_importe_por_mes(ventas_limpias):
    assert SalesMetrics(ventas_limpias).revenue_by_month() == {"2026-01": 250.0, "2026-02": 120.0}


def test_ticket_medio_y_unidades(ventas_limpias):
    metrics = SalesMetrics(ventas_limpias)
    assert metrics.average_ticket() == pytest.approx(92.5)
    assert metrics.total_units() == 17


def test_top_clientes(ventas_limpias):
    assert SalesMetrics(ventas_limpias).top_customers(1) == {"C1": 220.0}


def test_top_clientes_n_invalido(ventas_limpias):
    with pytest.raises(ValueError):
        SalesMetrics(ventas_limpias).top_customers(0)


def test_agrupar_por_columna_inexistente(ventas_limpias):
    with pytest.raises(KeyError):
        SalesMetrics(ventas_limpias).revenue_by("pais")


def test_sin_ventas_no_rompe(ventas_limpias):
    metrics = SalesMetrics(ventas_limpias.iloc[0:0])
    assert metrics.total_revenue() == 0.0
    assert metrics.average_ticket() == 0.0


def test_no_modifica_el_dataframe_original(ventas_limpias):
    columnas = list(ventas_limpias.columns)
    SalesMetrics(ventas_limpias).summary()
    assert list(ventas_limpias.columns) == columnas


def test_summary_tiene_todas_las_claves(ventas_limpias):
    summary = SalesMetrics(ventas_limpias).summary(top_n=2)
    assert summary["ventas_validas"] == 4
    assert len(summary["top_clientes"]) == 2
    assert isinstance(summary["importe_por_producto"], dict)
    assert not isinstance(summary["importe_total"], pd.Series)
