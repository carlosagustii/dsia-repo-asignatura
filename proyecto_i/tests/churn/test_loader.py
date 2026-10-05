import pytest

from churn_app.exceptions import DataLoadError, SchemaError
from churn_app.loader import REQUIRED_COLUMNS, CsvCustomerRepository, load_customers


def test_load_devuelve_clientes_con_esquema_completo(clientes_csv):
    frame = CsvCustomerRepository(clientes_csv).load()
    assert len(frame) == 4
    assert list(frame.columns) == list(REQUIRED_COLUMNS)


def test_load_no_convierte_tipos(clientes_csv):
    # TotalCharges en blanco debe llegar intacto: lo decide el validador, no el loader.
    frame = load_customers(clientes_csv)
    assert frame.loc[2, "TotalCharges"] == " "


def test_path_inexistente_lanza_error_de_dominio(tmp_path):
    with pytest.raises(DataLoadError, match="No existe"):
        load_customers(tmp_path / "no_existe.csv")


def test_fichero_vacio(tmp_path):
    path = tmp_path / "vacio.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(DataLoadError):
        load_customers(path)


def test_faltan_columnas(tmp_path):
    path = tmp_path / "parcial.csv"
    path.write_text("customerID,Churn\n0001-AAAAA,No\n", encoding="utf-8")
    with pytest.raises(SchemaError, match="tenure"):
        load_customers(path)
