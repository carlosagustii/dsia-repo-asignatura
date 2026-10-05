# Proyecto I — Programación avanzada en Python

[![proyecto-i-ci](https://github.com/carlosagustii/dsia-repo-asignatura/actions/workflows/proyecto_i.yml/badge.svg)](https://github.com/carlosagustii/dsia-repo-asignatura/actions/workflows/proyecto_i.yml)

Dos pipelines de calidad de datos con la misma arquitectura
(**carga → validación → métricas → CLI**), tests con pytest y CI en GitHub Actions.

| Parte | Paquete | Datos | Pregunta de negocio |
| --- | --- | --- | --- |
| **A** | `ventas_app/` | `data/ventas.csv` (curso) | ¿Cuánto vendemos, dónde, qué y a quién? |
| **B** | `churn_app/` | `data/telco_churn.csv` (IBM Telco Customer Churn) | ¿Cuántos clientes perdemos, cuánto dinero nos cuesta y en qué segmentos? |

La Parte B es además el **punto de partida de los Proyectos II y III** (ver [`ROADMAP.md`](ROADMAP.md)).

---

## Puesta en marcha

```bash
cd proyecto_i
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Parte A — Pipeline de ventas (`ventas_app`)

```bash
python -m ventas_app.cli --input data/ventas.csv
python -m ventas_app.cli --input data/ventas.csv --json --top 3
python -m ventas_app.cli --input data/ventas.csv \
    --output out/ventas_limpias.csv --rejected out/ventas_rechazadas.csv
```

**Reglas de validación** (`ventas_app/validator.py`). Una fila se rechaza si incumple
cualquiera; el CSV de rechazados incluye una columna `motivo` con *todas* las reglas que falla:

| Regla | Ejemplo rechazado |
| --- | --- |
| `fecha` con formato `YYYY-MM-DD` válido | `2026-13-01`, vacío |
| `region`, `producto`, `cliente_id` no vacíos | `" "` |
| `unidades` numéricas, enteras y > 0 | vacío, `na`, `0`, `-2`, `2.5` |
| `precio_unitario` numérico y > 0 | vacío, `0`, `-5.0` |

**Métricas**: importe total, unidades, ticket medio, importe por región, por producto,
por mes y top clientes.

**Checkpoint del curso:** `ventas.csv` → **140 válidas / 10 rechazadas** (cubierto por un test de integración).

## Parte B — Churn de clientes de una operadora (`churn_app`)

### Dataset

| | |
| --- | --- |
| Nombre | IBM Telco Customer Churn |
| URL de origen | <https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/data/Telco-Customer-Churn.csv> |
| Descarga directa | <https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv> |
| Licencia | Apache License 2.0 (repositorio de IBM). Datos ficticios de muestra publicados por IBM, sin datos personales reales |
| Fecha de descarga | 5 de octubre de 2026 |
| Tamaño | 7.043 clientes × 21 columnas (~950 KB, versionado en `data/`) |
| Regenerar | `python scripts/download_telco.py` (`--sample N` para una muestra) |

Cada fila es un cliente con suscripción mensual: datos demográficos, servicios contratados,
tipo de contrato, método de pago, cuota mensual (`MonthlyCharges`), facturación acumulada
(`TotalCharges`), antigüedad en meses (`tenure`) y si se ha dado de baja (`Churn`).

**Por qué este dataset:** el churn es *el* problema de negocio de cualquier empresa de
suscripción (SaaS, telco, fintech, streaming). Permite hablar de KPIs que se usan en
entrevistas y en el día a día (churn rate, MRR, ARPU, cohortes) y escala de forma natural a
un modelo predictivo (Proyecto II) y a un producto con API y dashboard (Proyecto III).

### Uso

```bash
python -m churn_app.cli --input data/telco_churn.csv
python -m churn_app.cli --segment PaymentMethod --json
python -m churn_app.cli --output out/clientes_limpios.csv --rejected out/clientes_rechazados.csv
```

`--segment` acepta: `Contract`, `InternetService`, `PaymentMethod`, `gender`, `SeniorCitizen`,
`Partner`, `Dependents`, `PaperlessBilling`, `TechSupport`, `OnlineSecurity`.

### Reglas de validación (`churn_app/validator.py`)

| Tipo | Regla |
| --- | --- |
| Formato | `customerID` con patrón `NNNN-XXXXX` |
| Unicidad | `customerID` no duplicado (se conserva la primera aparición) |
| Dominio cerrado | `Contract`, `PaymentMethod`, `InternetService`, `gender`, `Churn`, columnas Yes/No, `SeniorCitizen ∈ {0,1}`… |
| Rango | `tenure` entero en [0, 120]; `MonthlyCharges` en (0, 500] |
| Tipo | `TotalCharges` numérico y ≥ 0 |
| Coherencia | `TotalCharges / (tenure × MonthlyCharges)` en [0,5, 2] (admite cambios de tarifa) |
| Coherencia | Sin internet ⇒ servicios de internet = `No internet service`; sin teléfono ⇒ `No phone service` |

**Normalización documentada:** 11 clientes con `tenure = 0` (recién dados de alta) traen
`TotalCharges` vacío porque aún no se les ha facturado. No es un error: se imputa `0.0` y se
informa del número de imputaciones. Un `TotalCharges` vacío con `tenure > 0` sí se rechaza.

### Métricas

1. **Tasa de churn** global.
2. **Churn por segmento** (contrato, método de pago, servicio…).
3. **Churn por cohorte de antigüedad** (0-12, 13-24, 25-48, 49+ meses).
4. **MRR activo y MRR perdido** (ingresos mensuales recurrentes que se van con las bajas).
5. **ARPU** de clientes activos vs. bajas.

### Resultados sobre el dataset completo

```text
Clientes válidos: 7043 | rechazados: 0 | TotalCharges imputados: 11
Churn: 26.54 %
MRR activo: 316985.75 | MRR perdido: 139130.85 (30.50 %)
ARPU: activos 61.27, bajas 74.44

Churn por Contract:
  Month-to-month                42.71 %
  One year                      11.27 %
  Two year                       2.83 %

Churn por antigüedad:
  0-12 meses                    47.44 %
  13-24 meses                   28.71 %
  25-48 meses                   20.39 %
  49+ meses                      9.51 %
```

Lectura rápida: **1 de cada 4 clientes se va y se lleva el 30 % del MRR**; quienes se van
pagan *más* que la media (ARPU 74 vs 61). El riesgo se concentra en el **primer año** y en
**contratos mes a mes** (y, con `--segment PaymentMethod`, en el pago por *electronic check*:
45 %). Estas variables serán candidatas claras para el modelo del Proyecto II.

---

## Tests

```bash
pytest -q                                   # todo (91 tests)
pytest -q -m "not integration"              # solo unitarios (sin leer data/)
pytest -q -m integration                    # solo integración (CSV reales)
pytest --cov=ventas_app --cov=churn_app --cov-report=term-missing --cov-fail-under=60
```

| | Parte A | Parte B |
| --- | --- | --- |
| loader | `tests/ventas/test_loader.py` | `tests/churn/test_loader.py` |
| validator | `tests/ventas/test_validator.py` | `tests/churn/test_validator.py` |
| metrics | `tests/ventas/test_metrics.py` | `tests/churn/test_metrics.py` |
| cli | `tests/ventas/test_cli.py` | `tests/churn/test_cli.py` |
| integración | 140 / 10 en `ventas.csv` | 7.043 válidos, 11 imputados, churn 26,54 % |

Se usan los cuatro conceptos de clase: **AAA + assert**, **`pytest.raises`**
(paths inexistentes, ficheros vacíos, esquema incompleto), **`parametrize`** (bordes 0, -1,
nulos, textos, rangos) y **fixtures** (DataFrames en memoria y CSV en `tmp_path`).
Cobertura actual: **~97 %**.

## CI

Workflow: [`../.github/workflows/proyecto_i.yml`](../.github/workflows/proyecto_i.yml)
(en la raíz del repo, porque GitHub solo lee workflows de ahí).

Se ejecuta en cada `push` a `main` y en cada `pull_request`, con Python 3.12:
instala dependencias → tests unitarios → todos los tests con **gate de cobertura ≥ 60 %** →
smoke test de las dos CLI.

Último run: pestaña [Actions](https://github.com/carlosagustii/dsia-repo-asignatura/actions/workflows/proyecto_i.yml) (badge arriba).

## Estructura

```text
proyecto_i/
  ventas_app/            # Parte A
    exceptions.py loader.py validator.py metrics.py cli.py __main__.py
  churn_app/             # Parte B (mismo patrón, reglas y métricas propias)
    exceptions.py loader.py validator.py metrics.py cli.py __main__.py
  tests/
    ventas/  conftest.py test_loader.py test_validator.py test_metrics.py test_cli.py
    churn/   conftest.py test_loader.py test_validator.py test_metrics.py test_cli.py
  data/      ventas.csv telco_churn.csv
  scripts/   download_telco.py
  DESIGN.md  ROADMAP.md  AI_USAGE.md
  pytest.ini requirements.txt
```

Decisiones de diseño (SOLID, patrones): [`DESIGN.md`](DESIGN.md).
Uso de IA en el desarrollo: [`AI_USAGE.md`](AI_USAGE.md).
