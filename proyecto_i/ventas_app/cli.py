"""CLI del pipeline de ventas.

Ejemplos::

    python -m ventas_app.cli --input data/ventas.csv
    python -m ventas_app.cli --input data/ventas.csv \\
        --output out/ventas_limpias.csv --rejected out/ventas_rechazadas.csv --json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Sequence

from ventas_app.exceptions import VentasError
from ventas_app.loader import CsvSalesRepository
from ventas_app.metrics import SalesMetrics
from ventas_app.validator import SalesValidator

logger = logging.getLogger("ventas_app")

EXIT_OK = 0
EXIT_DATA_ERROR = 1


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ventas_app",
        description="Valida un CSV de ventas y calcula métricas de negocio.",
    )
    parser.add_argument("--input", type=Path, default=Path("data/ventas.csv"), help="CSV de entrada")
    parser.add_argument("--output", type=Path, help="CSV donde guardar las filas válidas")
    parser.add_argument("--rejected", type=Path, help="CSV donde guardar las filas rechazadas")
    parser.add_argument("--top", type=int, default=5, help="Nº de clientes en el top (def. 5)")
    parser.add_argument("--json", action="store_true", help="Imprime el informe en JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Logs en nivel DEBUG")
    args = parser.parse_args(argv)
    if args.top <= 0:
        parser.error("--top debe ser un entero positivo")
    return args


def _write_csv(frame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    logger.info("Guardadas %d filas en %s", len(frame), path)


def format_report(report: dict[str, object]) -> str:
    """Informe legible en texto plano."""
    lines = [
        f"Ventas válidas: {report['ventas_validas']} | rechazadas: {report['ventas_rechazadas']}",
        f"Importe total: {report['importe_total']:.2f} €",
        f"Unidades: {report['unidades_totales']} | Ticket medio: {report['ticket_medio']:.2f} €",
    ]
    for title, key in (
        ("Importe por región", "importe_por_region"),
        ("Importe por producto", "importe_por_producto"),
        ("Importe por mes", "importe_por_mes"),
        ("Top clientes", "top_clientes"),
    ):
        lines.append(f"\n{title}:")
        lines.extend(f"  {name:<12} {value:>10.2f}" for name, value in report[key].items())
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, object]:
    """Ejecuta el pipeline completo y devuelve el informe (sin imprimir)."""
    frame = CsvSalesRepository(args.input).load()
    result = SalesValidator().validate(frame)
    logger.info("Válidas: %d | rechazadas: %d", result.n_valid, result.n_invalid)

    if args.output:
        _write_csv(result.valid, args.output)
    if args.rejected:
        _write_csv(result.invalid, args.rejected)

    report = SalesMetrics(result.valid).summary(top_n=args.top)
    report["ventas_rechazadas"] = result.n_invalid
    return report


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        report = run(args)
    except VentasError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_DATA_ERROR

    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else format_report(report))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
