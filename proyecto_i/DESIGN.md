# Diseño

Ambos paquetes siguen el mismo flujo, con una responsabilidad por módulo:

```text
CsvXRepository.load()  →  XValidator.validate()  →  XMetrics.summary()  →  cli.main()
   (loader.py)              (validator.py)            (metrics.py)          (cli.py)
   DataFrame en crudo       ValidationResult          dict serializable     texto / JSON / CSV
                            (válidas tipadas +
                             rechazadas con motivo)
```

## SOLID aplicado

| Principio | Dónde | Por qué cumple |
| --- | --- | --- |
| **SRP** | `loader.py` / `validator.py` / `metrics.py` / `cli.py` | El loader solo lee y comprueba el esquema (todo como texto); el validador decide qué es válido y convierte tipos; las métricas solo agregan; la CLI solo orquesta y presenta. |
| **OCP** | `DEFAULT_RULES` en ambos `validator.py` | Cada regla es una función `DataFrame → Series[bool]`. Añadir una regla es añadir una entrada al diccionario, sin modificar `validate()`. Los tests inyectan reglas propias (`test_reglas_personalizadas_open_closed`). |
| **DIP** | `SalesRepository` / `CustomerRepository` (`typing.Protocol`) | El resto del pipeline depende de “algo con `load() -> DataFrame`”, no del CSV. En el Proyecto II/III se podrá cambiar a base de datos o API sin tocar validación ni métricas. |
| **LSP** | `SchemaError(DataLoadError)` | Un esquema incompleto es un caso particular de error de carga: quien captura `DataLoadError` también lo gestiona correctamente. |
| **ISP** | Protocols de un solo método | Los repositorios solo exigen `load()`; nadie depende de métodos que no usa. |

## Patrones

- **Repository** — `CsvSalesRepository`, `CsvCustomerRepository`.
- **Strategy** — reglas de validación intercambiables (`rules=` en el constructor del validador).
- **Pipeline stages** — `run()` en cada `cli.py` encadena carga → validación → métricas.
- **Value object** — `ValidationResult` (dataclass `frozen`), resultado inmutable de validar.

## Errores

Cada paquete tiene su jerarquía (`VentasError` / `ChurnAppError` → `DataLoadError` →
`SchemaError`, y `ValidationError`). La CLI captura la raíz, escribe un mensaje claro en
`stderr` y devuelve código de salida `1` en lugar de un traceback. Los argumentos inválidos
los rechaza `argparse` (código `2`).

## Reutilización A ↔ B sin acoplamiento

La Parte B reutiliza **las ideas** de la A (módulos, jerarquía de excepciones, reglas como
funciones, `ValidationResult`, CLI con `--output/--rejected/--json`), pero los paquetes son
independientes: ninguno importa del otro. Se ha preferido duplicar ~20 líneas (el bucle de
`validate()`) antes que crear un paquete común prematuro; si en el Proyecto II aparece un
tercer pipeline, ese bucle se extraería a un módulo `core`.

Diferencias propias del dominio de churn:

- **Reglas de coherencia entre columnas** (servicios contratados, facturación acumulada vs. cuota × meses), no solo de cada campo aislado.
- **Imputación justificada** (`TotalCharges` vacío en clientes con `tenure = 0`), contabilizada aparte en lugar de rechazar clientes válidos.
- **KPIs de suscripción** (churn, MRR, ARPU, cohortes) en lugar de sumas de importes.

## Clean Code

- Sin números mágicos: `MAX_TENURE_MONTHS`, `MAX_MONTHLY_CHARGE`, `TOTAL_CHARGES_RATIO`, `TENURE_BINS`…
- `logging` para diagnóstico (`-v` para verlo) y `print` solo para el informe final.
- `main(argv)` recibe los argumentos: la CLI se prueba sin subprocesos ni rutas de la máquina.
