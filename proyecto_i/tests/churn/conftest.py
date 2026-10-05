import pandas as pd
import pytest

from churn_app.loader import REQUIRED_COLUMNS

CLIENTE_BASE = {
    "customerID": "0001-AAAAA",
    "gender": "Female",
    "SeniorCitizen": "0",
    "Partner": "Yes",
    "Dependents": "No",
    "tenure": "10",
    "PhoneService": "Yes",
    "MultipleLines": "No",
    "InternetService": "DSL",
    "OnlineSecurity": "No",
    "OnlineBackup": "Yes",
    "DeviceProtection": "No",
    "TechSupport": "No",
    "StreamingTV": "No",
    "StreamingMovies": "No",
    "Contract": "Month-to-month",
    "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check",
    "MonthlyCharges": "50.0",
    "TotalCharges": "500.0",
    "Churn": "No",
}


def make_customer(**overrides) -> dict[str, str]:
    """Cliente válido en crudo (texto, como lo deja el loader) con cambios puntuales."""
    return {**CLIENTE_BASE, **overrides}


@pytest.fixture
def cliente():
    return make_customer


@pytest.fixture
def clientes_crudos() -> pd.DataFrame:
    """4 clientes: 2 válidos, 1 nuevo con TotalCharges vacío (se imputa), 1 inválido."""
    return pd.DataFrame(
        [
            make_customer(),
            make_customer(customerID="0002-BBBBB", Churn="Yes"),
            make_customer(customerID="0003-CCCCC", tenure="0", TotalCharges=" "),
            make_customer(customerID="0004-DDDDD", MonthlyCharges="-3"),
        ]
    )


@pytest.fixture
def clientes_limpios() -> pd.DataFrame:
    """Clientes ya validados y tipados con resultados calculables a mano."""
    return pd.DataFrame(
        {
            "customerID": ["0001-AAAAA", "0002-BBBBB", "0003-CCCCC", "0004-DDDDD"],
            "Contract": ["Month-to-month", "Month-to-month", "Two year", "Two year"],
            "tenure": [2, 5, 30, 60],
            "MonthlyCharges": [80.0, 70.0, 50.0, 20.0],
            "Churn": [True, False, False, False],
        }
    )


@pytest.fixture
def clientes_csv(tmp_path, clientes_crudos):
    path = tmp_path / "clientes.csv"
    clientes_crudos[list(REQUIRED_COLUMNS)].to_csv(path, index=False)
    return path
