# Uso de herramientas de IA

Conforme a la política de la asignatura, se declara el uso de IA en este proyecto.

| Herramienta | Uso | Revisión humana |
| --- | --- | --- |
| Claude Code (Anthropic) | Propuesta del dominio de la Parte B y del dataset; generación inicial del código de `ventas_app` y `churn_app`, de los tests, del workflow de CI y de la documentación. | Pendiente de completar por el autor: qué se ha revisado, modificado o reescrito y por qué. |

## Cómo se ha verificado

- Ejecución de las dos CLI sobre los datos reales y comprobación de resultados
  (140/10 en `ventas.csv`; 7.043 clientes y churn 26,54 % en el dataset de IBM).
- `pytest` (91 tests) y cobertura ~97 %, en local y en GitHub Actions.

> Nota para el autor: completa la columna de revisión y añade cualquier otra herramienta
> que uses (Copilot, ChatGPT, Cursor…). El uso de IA sin citar se considera plagio.
