import pandas as pd
import pytest

from ventas_app.exceptions import ValidationError
from ventas_app.validator import REASON_COLUMN, SalesValidator


def _fila(**overrides) -> pd.DataFrame:
    base = {
        "fecha": "2026-01-01",
        "region": "Norte",
        "producto": "Gateway",
        "unidades": "3",
        "precio_unitario": "10.0",
        "cliente_id": "C1",
    }
    base.update(overrides)
    return pd.DataFrame([base])


def test_separa_validas_e_invalidas(ventas_mini):
    result = SalesValidator().validate(ventas_mini)
    assert result.n_valid == 1
    assert result.n_invalid == 2
    assert result.invalid_ratio == pytest.approx(2 / 3)


def test_filas_validas_salen_tipadas(ventas_mini):
    valid = SalesValidator().validate(ventas_mini).valid
    assert valid["unidades"].dtype == "int64"
    assert valid["precio_unitario"].dtype == "float64"
    assert pd.api.types.is_datetime64_any_dtype(valid["fecha"])


@pytest.mark.parametrize(
    ("precio", "es_valida"),
    [("0", False), ("-1", False), ("", False), ("abc", False), ("1", True), ("0.01", True)],
)
def test_bordes_de_precio(precio, es_valida):
    result = SalesValidator().validate(_fila(precio_unitario=precio))
    assert (result.n_valid == 1) is es_valida


@pytest.mark.parametrize(
    ("unidades", "es_valida"),
    [("0", False), ("-2", False), ("", False), ("na", False), ("2.5", False), ("1", True)],
)
def test_bordes_de_unidades(unidades, es_valida):
    result = SalesValidator().validate(_fila(unidades=unidades))
    assert (result.n_valid == 1) is es_valida


@pytest.mark.parametrize(
    "campo, valor", [("fecha", "2026-13-01"), ("fecha", ""), ("region", " "), ("cliente_id", "")]
)
def test_campos_obligatorios_y_fecha(campo, valor):
    result = SalesValidator().validate(_fila(**{campo: valor}))
    assert result.n_invalid == 1


def test_motivo_acumula_todas_las_reglas_incumplidas():
    result = SalesValidator().validate(_fila(unidades="0", precio_unitario="-1"))
    motivo = result.invalid.iloc[0][REASON_COLUMN]
    assert "unidades" in motivo and "precio" in motivo


def test_reglas_personalizadas_open_closed():
    solo_norte = {"región distinta de Norte": lambda df: df["region"] != "Norte"}
    result = SalesValidator(rules=solo_norte).validate(_fila(region="Sur"))
    assert result.invalid.iloc[0][REASON_COLUMN] == "región distinta de Norte"


def test_sin_reglas_todo_es_valido():
    assert SalesValidator(rules={}).validate(_fila(unidades="-5")).n_valid == 1


def test_falta_columna_lanza_validation_error():
    with pytest.raises(ValidationError):
        SalesValidator().validate(pd.DataFrame({"fecha": ["2026-01-01"]}))
