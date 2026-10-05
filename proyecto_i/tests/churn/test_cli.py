import json
from pathlib import Path

import pandas as pd
import pytest

from churn_app import cli

DATA = Path(__file__).resolve().parents[2] / "data" / "telco_churn.csv"


def test_parse_args_por_defecto():
    args = cli.parse_args([])
    assert args.input == Path("data/telco_churn.csv")
    assert args.segment == "Contract"


def test_parse_args_rechaza_segmento_no_permitido():
    with pytest.raises(SystemExit):
        cli.parse_args(["--segment", "customerID"])


def test_main_informe_texto(clientes_csv, capsys):
    assert cli.main(["--input", str(clientes_csv)]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "Clientes válidos: 3 | rechazados: 1 | TotalCharges imputados: 1" in out
    assert "Churn por Contract" in out


def test_main_json_y_salidas(clientes_csv, tmp_path, capsys):
    limpios, rechazados = tmp_path / "o" / "ok.csv", tmp_path / "o" / "ko.csv"
    code = cli.main(
        [
            "--input",
            str(clientes_csv),
            "--segment",
            "PaymentMethod",
            "--output",
            str(limpios),
            "--rejected",
            str(rechazados),
            "--json",
        ]
    )
    report = json.loads(capsys.readouterr().out)
    assert code == 0
    assert report["segmento"] == "PaymentMethod"
    assert len(pd.read_csv(limpios)) == 3
    assert pd.read_csv(rechazados)["motivo"].str.contains("MonthlyCharges").all()


def test_main_error_de_datos(tmp_path, capsys):
    assert cli.main(["--input", str(tmp_path / "x.csv")]) == cli.EXIT_DATA_ERROR
    assert "Error" in capsys.readouterr().err


@pytest.mark.integration
def test_dataset_real_ibm_telco(capsys):
    assert cli.main(["--input", str(DATA), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["clientes_validos"] == 7043
    assert report["clientes_rechazados"] == 0
    assert report["imputados"] == 11
    assert report["churn_pct"] == pytest.approx(26.54)
