import pytest

from churn_app.metrics import ChurnMetrics


def test_churn_rate_global(clientes_limpios):
    assert ChurnMetrics(clientes_limpios).churn_rate() == 25.0


def test_churn_por_contrato(clientes_limpios):
    assert ChurnMetrics(clientes_limpios).churn_rate_by("Contract") == {
        "Month-to-month": 50.0,
        "Two year": 0.0,
    }


def test_mrr_activo_y_perdido(clientes_limpios):
    metrics = ChurnMetrics(clientes_limpios)
    assert metrics.mrr() == 140.0  # 70 + 50 + 20
    assert metrics.lost_mrr() == 80.0
    assert metrics.lost_mrr_pct() == pytest.approx(36.36)


def test_arpu_activos_vs_bajas(clientes_limpios):
    assert ChurnMetrics(clientes_limpios).arpu_by_churn() == {"activos": 46.67, "bajas": 80.0}


def test_churn_por_cohorte_incluye_cohortes_vacias(clientes_limpios):
    cohorts = ChurnMetrics(clientes_limpios).churn_by_tenure_cohort()
    assert cohorts == {
        "0-12 meses": 50.0,
        "13-24 meses": 0.0,
        "25-48 meses": 0.0,
        "49+ meses": 0.0,
    }


def test_segmento_desconocido(clientes_limpios):
    with pytest.raises(KeyError):
        ChurnMetrics(clientes_limpios).churn_rate_by("Planeta")


def test_sin_clientes(clientes_limpios):
    vacio = ChurnMetrics(clientes_limpios.iloc[0:0])
    assert vacio.churn_rate() == 0.0
    assert vacio.lost_mrr_pct() == 0.0


def test_summary(clientes_limpios):
    summary = ChurnMetrics(clientes_limpios).summary(segment="Contract")
    assert summary["clientes_validos"] == 4
    assert summary["segmento"] == "Contract"
    assert set(summary["churn_pct_por_antiguedad"]) == {
        "0-12 meses",
        "13-24 meses",
        "25-48 meses",
        "49+ meses",
    }
