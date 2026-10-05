import pytest

from ventas_app.exceptions import DataLoadError, SchemaError
from ventas_app.loader import REQUIRED_COLUMNS, CsvSalesRepository, load_sales


def test_load_devuelve_todas_las_filas_y_columnas(ventas_csv):
    # Arrange
    repo = CsvSalesRepository(ventas_csv)
    # Act
    frame = repo.load()
    # Assert
    assert len(frame) == 3
    assert set(REQUIRED_COLUMNS) <= set(frame.columns)


def test_load_conserva_valores_en_crudo_para_el_validador(ventas_csv):
    frame = load_sales(ventas_csv)
    assert frame.loc[2, "unidades"] == "na"


def test_path_inexistente_lanza_error_de_dominio(tmp_path):
    with pytest.raises(DataLoadError, match="No existe"):
        load_sales(tmp_path / "no_existe.csv")


def test_fichero_vacio_lanza_error_de_dominio(tmp_path):
    path = tmp_path / "vacio.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(DataLoadError, match="vacío"):
        load_sales(path)


def test_faltan_columnas_lanza_schema_error(tmp_path):
    path = tmp_path / "incompleto.csv"
    path.write_text("fecha,region\n2026-01-01,Norte\n", encoding="utf-8")
    with pytest.raises(SchemaError, match="unidades"):
        load_sales(path)
