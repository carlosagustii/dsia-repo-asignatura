import pandas as pd
import pytest

HEADER = "fecha,region,producto,unidades,precio_unitario,cliente_id\n"


@pytest.fixture
def ventas_mini() -> pd.DataFrame:
    """3 filas en crudo (como las deja el loader): 1 válida, 2 inválidas."""
    return pd.DataFrame(
        {
            "fecha": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "region": ["Norte", "Sur", "Norte"],
            "producto": ["A", "B", "A"],
            "unidades": ["2", "", "5"],
            "precio_unitario": ["10.0", "20.0", "-1.0"],
            "cliente_id": ["C1", "C2", "C1"],
        }
    )


@pytest.fixture
def ventas_limpias() -> pd.DataFrame:
    """Ventas ya validadas y tipadas, con totales fáciles de calcular a mano."""
    return pd.DataFrame(
        {
            "fecha": pd.to_datetime(["2026-01-05", "2026-01-20", "2026-02-01", "2026-02-10"]),
            "region": ["Norte", "Sur", "Norte", "Este"],
            "producto": ["Gateway", "Sensor A", "Sensor A", "Gateway"],
            "unidades": [2, 10, 4, 1],
            "precio_unitario": [100.0, 5.0, 5.0, 100.0],
            "cliente_id": ["C1", "C2", "C1", "C3"],
        }
    )


@pytest.fixture
def ventas_csv(tmp_path):
    """CSV pequeño en disco (2 válidas + 1 inválida) para loader y CLI."""
    path = tmp_path / "ventas.csv"
    path.write_text(
        HEADER
        + "2026-01-01,Norte,Gateway,2,100.0,C1\n"
        + "2026-01-15,Sur,Sensor A,10,5.0,C2\n"
        + "2026-01-20,Sur,Sensor A,na,5.0,C3\n",
        encoding="utf-8",
    )
    return path
