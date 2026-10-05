# Hoja de ruta: de Proyecto I a Trabajo Final

**Tema:** *Retención de clientes en un negocio de suscripción* — detectar qué clientes
van a darse de baja, cuánto dinero está en riesgo y qué hacer con cada uno.

Por qué es un buen tema para portfolio:

- Es un problema real y transversal: SaaS, telcos, bancos, seguros, streaming, gimnasios…
  Cualquier entrevistador lo entiende en 10 segundos.
- Combina analítica de negocio (MRR, cohortes), ML clásico (clasificación con datos
  desbalanceados) e IA generativa con un uso **útil**, no decorativo.
- El resultado final es un producto demostrable: API + dashboard.

## Proyecto I (este) — calidad de datos y KPIs

- [x] Pipeline `churn_app`: carga, validación con reglas de dominio, KPIs de churn y MRR, CLI.
- [x] Tests + CI.

## Proyecto II (octubre) — modelo + IA generativa

Mismo dominio y dataset, en **un repo nuevo** (el del Trabajo Final):

1. Reutilizar `loader` + `validator` de `churn_app` como etapa de ingesta.
2. **Modelo scikit-learn**: clasificador de churn (`LogisticRegression` como baseline
   interpretable y `RandomForest`/`HistGradientBoosting` para comparar) con `Pipeline` +
   `ColumnTransformer` (one-hot de categóricas, escalado de numéricas).
   - Métricas adecuadas a clases desbalanceadas (26 % positivos): ROC-AUC, PR-AUC, recall de la clase churn, matriz de confusión.
   - Persistencia con `joblib` y `train.py` reproducible (`random_state`, split estratificado).
   - Inferencia en el pipeline: puntuar a cada cliente activo → `prob_churn` + **MRR en riesgo** (`prob × MonthlyCharges`).
3. **IA generativa** (cliente con modo `mock` + proveedor real): a partir del perfil y de
   los factores de riesgo de un cliente, generar un **plan de retención** (acción recomendada,
   argumento para el equipo de atención al cliente y borrador de email).
4. Logs, `.env.example`, `AI_USAGE.md`, tests del modelo con un fixture pequeño.

## Proyecto III (noviembre) — producto end-to-end

- **API** (FastAPI o Flask): `/health`, `/predict` (probabilidad de churn de un cliente),
  `/analyze` (plan de retención con IA), `/metrics` (KPIs del Proyecto I).
- **Dashboard** (Streamlit o Dash): KPIs de churn y MRR, ranking de clientes con más MRR en
  riesgo, ficha de cliente con predicción + plan de retención generado.
- Docker + despliegue (Render / Railway / Hugging Face Spaces), CI completo, logging y monitorización básica (latencia, nº de predicciones, distribución de probabilidades).
- Demo de 5-7 min: “de un CSV a un panel que dice a quién llamar hoy y qué decirle”.
