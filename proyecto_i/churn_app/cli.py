"""CLI del pipeline de churn.

Ejemplos::

    python -m churn_app.cli --input data/telco_churn.csv
    python -m churn_app.cli --segment PaymentMethod --json
    python -m churn_app.cli --output out/clientes_limpios.csv --rejected out/rechazados.csv
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Sequence

from churn_app.exceptions import ChurnAppError
from churn_app.loader import CsvCustomerRepository
from churn_app.metrics import SEGMENT_COLUMNS, ChurnMetrics
from churn_app.validator import CustomerValidator

logger = logging.getLogger("churn_app")

EXIT_OK = 0
EXIT_DATA_ERROR = 1


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="churn_app",
        description="Valida la base de clientes y calcula KPIs de churn y MRR.",
    )
    parser.add_argument(
        "--input", type=Path, default=Path("data/telco_churn.csv"), help="CSV de clientes"
    )
    parser.add_argument("--output", type=Path, help="CSV donde guardar los clientes válidos")
    parser.add_argument("--rejected", type=Path, help="CSV donde guardar los rechazados")
    parser.add_argument(
        "--segment",
        choices=SEGMENT_COLUMNS,
        default="Contract",
        help="Columna para desglosar el churn (def. Contract)",
    )
    parser.add_argument("--json", action="store_true", help="Imprime el informe en JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Logs en nivel DEBUG")
    return parser.parse_args(argv)


def _write_csv(frame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    logger.info("Guardadas %d filas en %s", len(frame), path)


def format_report(report: dict[str, object]) -> str:
    lines = [
        f"Clientes válidos: {report['clientes_validos']} | rechazados: "
        f"{report['clientes_rechazados']} | TotalCharges imputados: {report['imputados']}",
        f"Churn: {report['churn_pct']:.2f} %",
        f"MRR activo: {report['mrr_activo']:.2f} | MRR perdido: {report['mrr_perdido']:.2f} "
        f"({report['mrr_perdido_pct']:.2f} %)",
        "ARPU: " + ", ".join(f"{k} {v:.2f}" for k, v in report["arpu"].items()),
        f"\nChurn por {report['segmento']}:",
    ]
    lines.extend(f"  {k:<28} {v:>6.2f} %" for k, v in report["churn_pct_por_segmento"].items())
    lines.append("\nChurn por antigüedad:")
    lines.extend(f"  {k:<28} {v:>6.2f} %" for k, v in report["churn_pct_por_antiguedad"].items())
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, object]:
    frame = CsvCustomerRepository(args.input).load()
    result = CustomerValidator().validate(frame)
    logger.info(
        "Válidos: %d | rechazados: %d | imputados: %d",
        result.n_valid,
        result.n_invalid,
        result.n_imputed,
    )
    if args.output:
        _write_csv(result.valid, args.output)
    if args.rejected:
        _write_csv(result.invalid, args.rejected)

    report = ChurnMetrics(result.valid).summary(segment=args.segment)
    report["clientes_rechazados"] = result.n_invalid
    report["imputados"] = result.n_imputed
    return report


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        report = run(args)
    except ChurnAppError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_DATA_ERROR

    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else format_report(report))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
