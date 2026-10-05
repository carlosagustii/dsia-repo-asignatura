import pandas as pd
import pytest

from churn_app.exceptions import ValidationError
from churn_app.validator import REASON_COLUMN, CustomerValidator


def _validar(*clientes):
    return CustomerValidator().validate(pd.DataFrame(list(clientes)))


def test_separa_validos_invalidos_e_imputados(clientes_crudos):
    result = CustomerValidator().validate(clientes_crudos)
    assert (result.n_valid, result.n_invalid, result.n_imputed) == (3, 1, 1)


def test_cliente_nuevo_sin_factura_se_imputa_a_cero(clientes_crudos):
    valid = CustomerValidator().validate(clientes_crudos).valid
    nuevo = valid.set_index("customerID").loc["0003-CCCCC"]
    assert nuevo["TotalCharges"] == 0.0


def test_tipos_de_salida(clientes_crudos):
    valid = CustomerValidator().validate(clientes_crudos).valid
    assert valid["Churn"].dtype == bool
    assert valid["tenure"].dtype == "int64"
    assert valid["MonthlyCharges"].dtype == "float64"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("customerID", "1234"),
        ("customerID", ""),
        ("tenure", "-1"),
        ("tenure", "121"),
        ("tenure", "3.5"),
        ("tenure", "abc"),
        ("MonthlyCharges", "0"),
        ("MonthlyCharges", "999"),
        ("TotalCharges", "-10"),
        ("TotalCharges", "n/a"),
        ("Contract", "Weekly"),
        ("Churn", "Maybe"),
        ("gender", ""),
        ("SeniorCitizen", "2"),
        ("PaymentMethod", "Bitcoin"),
    ],
)
def test_reglas_de_tipo_rango_y_dominio(cliente, campo, valor):
    assert _validar(cliente(**{campo: valor})).n_invalid == 1


@pytest.mark.parametrize("tenure", ["0", "1", "72", "120"])
def test_bordes_validos_de_tenure(cliente, tenure):
    total = str(float(tenure) * 50.0) if tenure != "0" else ""
    assert _validar(cliente(tenure=tenure, TotalCharges=total)).n_valid == 1


def test_total_vacio_con_antiguedad_es_invalido(cliente):
    assert _validar(cliente(tenure="5", TotalCharges="")).n_invalid == 1


def test_total_incoherente_con_cuota_y_antiguedad(cliente):
    # 10 meses x 50 € = 500 esperados; 5000 está fuera de tolerancia.
    result = _validar(cliente(TotalCharges="5000"))
    assert "incoherente" in result.invalid.iloc[0][REASON_COLUMN]


def test_sin_internet_pero_con_servicios_de_internet(cliente):
    result = _validar(cliente(InternetService="No"))  # addons siguen en Yes/No
    assert result.invalid.iloc[0][REASON_COLUMN] == "servicios incoherentes"


def test_sin_telefono_coherente_es_valido(cliente):
    assert _validar(cliente(PhoneService="No", MultipleLines="No phone service")).n_valid == 1


def test_customer_id_duplicado_conserva_el_primero(cliente):
    result = _validar(cliente(), cliente(Churn="Yes"))
    assert result.n_valid == 1
    assert result.valid.iloc[0]["Churn"] == False  # noqa: E712
    assert "duplicado" in result.invalid.iloc[0][REASON_COLUMN]


def test_falta_columna_lanza_validation_error():
    with pytest.raises(ValidationError):
        CustomerValidator().validate(pd.DataFrame({"customerID": ["0001-AAAAA"]}))


def test_reglas_inyectables(cliente):
    validator = CustomerValidator(rules={"solo bajas": lambda df: df["Churn"] != "Yes"})
    assert validator.validate(pd.DataFrame([cliente()])).n_invalid == 1
    assert CustomerValidator(rules={}).validate(pd.DataFrame([cliente(tenure="-9")])).n_valid == 1
