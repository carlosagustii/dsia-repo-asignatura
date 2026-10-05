"""Descarga el dataset IBM Telco Customer Churn a ``data/telco_churn.csv``.

Uso (desde ``proyecto_i/``)::

    python scripts/download_telco.py                 # dataset completo (7.043 filas, ~1 MB)
    python scripts/download_telco.py --sample 2000   # muestra reproducible

El CSV ya viene versionado en el repo; este script documenta su origen y
permite regenerarlo. No lo usan los tests (no deben depender de la red).
"""

from __future__ import annotations

import argparse
import io
import sys
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from churn_app.loader import SOURCE_URL  # noqa: E402

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "telco_churn.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sample", type=int, help="Nº de filas de una muestra aleatoria")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:  # noqa: S310
        raw = response.read().decode("utf-8")
    frame = pd.read_csv(io.StringIO(raw), dtype=str, keep_default_na=False)
    if args.sample:
        frame = frame.sample(n=min(args.sample, len(frame)), random_state=args.seed)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    print(f"Guardadas {len(frame)} filas en {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
