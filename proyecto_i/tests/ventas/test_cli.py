import json
from pathlib import Path

import pandas as pd
import pytest

from ventas_app import cli

DATA = Path(__file__).resolve().parents[2] / "data" / "ventas.csv"


def test_parse_args_valores_por_defecto():
    args = cli.parse_args([])
    assert args.input == Path("data/ventas.csv")
    assert args.top == 5 and args.json is False


def test_parse_args_rechaza_top_no_positivo():
    with pytest.raises(SystemExit):
        cli.parse_args(["--top", "0"])


def test_main_imprime_informe_texto(ventas_csv, capsys):
    exit_code = cli.main(["--input", str(ventas_csv)])
    out = capsys.readouterr().out
    assert exit_code == cli.EXIT_OK
    assert "Ventas válidas: 2 | rechazadas: 1" in out
    assert "Importe total: 250.00" in out


def test_main_json_y_ficheros_de_salida(ventas_csv, tmp_path, capsys):
    limpias = tmp_path / "out" / "limpias.csv"
    rechazadas = tmp_path / "out" / "rechazadas.csv"

    exit_code = cli.main(
        ["--input", str(ventas_csv), "--output", str(limpias), "--rejected", str(rechazadas), "--json"]
    )

    report = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert report["importe_total"] == 250.0
    assert len(pd.read_csv(limpias)) == 2
    assert "motivo" in pd.read_csv(rechazadas).columns


def test_main_con_fichero_inexistente_devuelve_error(tmp_path, capsys):
    exit_code = cli.main(["--input", str(tmp_path / "nada.csv")])
    assert exit_code == cli.EXIT_DATA_ERROR
    assert "No existe" in capsys.readouterr().err


@pytest.mark.integration
def test_csv_curso_tiene_140_validas_y_10_invalidas(capsys):
    exit_code = cli.main(["--input", str(DATA), "--json"])
    report = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert report["ventas_validas"] == 140
    assert report["ventas_rechazadas"] == 10
