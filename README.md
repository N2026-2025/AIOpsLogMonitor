# AIOps Log Monitor / Legacy-Bridge — Arquitectura y documentación

## 1. Visión General

**AIOps** (observabilidad y triaje inteligente de logs de sistemas legacy/legacy bridge). Implementa la metodología **STAR**: observabilidad de sistemas heredados + triaje inteligente con ML explicable.

- **Presupuesto IT**: Según Accenture/Thoughtworks 2026, hasta el 70% del presupuesto IT mantiene sistemas heredados.
- **Generación de logs**: Miles de eventos por minuto en sistemas en la nube y on-premise.
- **Problema**: Equipos de soporte/QA/dev pierden horas revisando logs manuales para descubrir caídas de servicio.
- **Riesgo**: Degradaciones silenciosas (picos de latencia) disparan costos de servidores sin ser detectadas.

## 2. Solución Arquitectónica

| Capa | Componente | Tecnología | Propósito |
|------|-----------|-----------|----------|
| **Ingesta** | Pipeline Python | `src/ingestion/parse.py`, `src/ingestion/features.py` | Limpieza CSV, feature engineering, normalización |
| **Almacenamiento** | SQL | `src/storage/models.py`, `src/storage/db.py`, PostgreSQL | Esquema por entorno/instancia/servicio |
| **Modelado** | ML interpretables | `src/ml/train.py` (RandomForest + IsolationForest) | Predicción fallos, severidad, anomalías |
| **Explicabilidad** | SHAP + árbol | `src/ml/explain.py` | SHAP values, decision paths, no black box |
| **API REST** | FastAPI | `src/api/main.py` | Endpoints health/predict/explain/ingest/events/incidents |
| **Persistencia** | Artefactos | `src/artifacts/aioplogmonitor_models_v0.1.0.pkl` | Serialización joblib |

## 3. Arquitectura (STAR)

```
[Legacy / fuentes de logs] --\> [Ingestion Service] --\> [PostgreSQL]
                                  |
[Dataset de entrenamiento] --/ [ML Pipeline] --/ [Modelos interpretables]
                                  |
[API REST (FastAPI)] <--> [ML Pipeline] <--> [Explicabilidad (SHAP)]
                                  |
[Usuario / Soporte] --\> [Consulta incidentes priorizados]
```

### Decisiones clave:

| Aspecto | Decisión | Justificación |
|---------|----------|---------------|
| **ML** | RandomForest + IsolationForest | Interpretables, features mixtas, buen baseline |
| **Explicabilidad** | SHAP TreeExplainer + decision path | Valores SHAP exactos para árboles, path legible |
| **Features** | Ingeniería manual (no autoencoder) | Control total, trazabilidad, bajo dimensionalidad |
| **API** | FastAPI | Async, validación Pydantic, OpenAPI auto |
| **DB** | PostgreSQL + SQLAlchemy 2.0 | Robusto, migraciones, consultas complejas |
| **Serialización** | joblib | Compatible sklearn, compacto |

## 4. Documentación del Proyecto

### Estructura de docs:

```
docs/
├── ARCHITECTURE.md — HLD: stack, contenedores, decisiones de diseño
├── LLD.md — LLD: módulos, esquema SQL, contrato API, flujos
├── API_CONTRACT.md — Esquema petición/respuesta endpoints REST
├── SETUP.md — Instalación y arranque paso a paso
├── observability/ — métricas, tracing, alerting
├── security/ — gitleaks, semgrep, trivy configs
├── scripts/ — seed_deterministic.py, scripts diversos
└── ARCHITECTURE.md — diseño técnico
```

### Evidencia disponible:

- `docs/ARCHITECTURE.md` — diseño arquitectónico completo
- `docs/LLD.md` — diseño detallado, esquema SQL, endpoints
- `docs/API_CONTRACT.md` — contrato de API con parámetros y respuestas
- `docs/SETUP.md` — guía de instalación y arranque
- `observability/` — métricas Prometheus, alerting rules OpenTelemetry
- `.github/workflows/ci.yml` — pipeline CI/CD completo
- `.gitleaks.toml`, `.semgrep.yml`, `.trivy.yaml` — seguridad

## 5. Guía de Instalación y Arranque

### Requisitos previos:

```bash
python >= 3.11
pip (gestor de paquetes Python)
Docker (opcional, para PostgreSQL)
Git (para clonar repositorio)
```

### Instalación de dependencias:

```bash
pip install -r requirements.txt
```

> **Recomendación: entorno virtual.** Para aislar las dependencias del proyecto del resto del sistema,
> crea y activa un `.venv` antes de instalar:
>
> ```bash
> # Crear entorno virtual
> python -m venv .venv
>
> # Activar (Windows PowerShell / cmd):
> .venv\Scripts\activate
> # Activar (Linux / macOS):
> source .venv/bin/activate
>
> # Ahora sí instalar dependencias
> pip install -r requirements.txt
> ```
>
> El entorno virtual se ignora con Git (`/.venv` está en `.gitignore`).</arg_value>

### Paso a paso:

1. **Inicializar base de datos**:

   ```bash
   python -m src.storage.init init
   ```

2. **Ingerir datos de ejemplo**:

   ```bash
   python -m src.ingestion.parse data/sample.csv
   ```

3. **Semilla determinista** (para CI/CD, tests y demos):

   ```bash
   python scripts/seed_deterministic.py
   ```

4. **Entrenar modelos**:

   ```bash
   python -m src.ml.train
   ```

   - Guarda artefactos en: `src/artifacts/aioplogmonitor_models_v0.1.0.pkl`
   - Métricas: accuracy fallo = 1.0

5. **Arrancar API**:

   ```bash
   python -m src.api.main
   ```

   - Servidor: `http://localhost:8000`
   - Alternativa: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`

### Verificar servicio:

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","timestamp":"..."}
```

## 5b. Análisis Exploratorio de Datos (EDA)

El análisis exploratorio de los datos se realiza sobre `data/processed_events_analysis.csv`
(1746 filas x 35 columnas). Los resultados y gráficos generados se guardan en `docs/eda/`.

```bash
# Ejecutar el script de EDA (genera PNGs en docs/eda/)
python scripts/eda.py

# Notebook interactivo (se exporta a scripts/eda.py para reproducibilidad)
notebooks/eda.ipynb
```

### Hallazgos clave del EDA

| Aspecto | Resultado |
|---|---|
| **Valores faltantes** | `message`, `file`, `line`, `logger_name`, `level` tienen 1677 nulos; `method`, `path`, `status_code`, `duration_ms` 1202 nulos (solo eventos HTTP) |
| **Rango numérico** | `duration_ms`: 0–5037 ms (media 269); `status_code`: 200–504; `hour`: 5–14 |
| **Distribución status** | SUCCESS 1275 (73%), FAILURE 471 (27%) |
| **Distribución severity** | LOW 912, MEDIUM 717, HIGH 117 |
| **Palabras frecuentes en message** | `on`, `exception`, `get`, `db`, `constraint`, `connection`, `timeout` |
| **Feature importance (RF, target=FAILURE)** | `event_type` 0.50, `severity` 0.20, `method` 0.08, `category` 0.08, `status_code` 0.07 |

Los gráficos generados son: `missing_values.png`, `numeric_distributions.png`,
`status_distribution.png`, `severity_distribution.png`, `event_type_distribution.png`,
`category_distribution.png`, `environment_distribution.png`, `correlation_matrix.png`,
`message_word_frequencies.png`, `feature_importance.png`.

## 6. API REST Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Healthcheck |
| GET | `/api/v1/health` | Healthcheck (proxy) |
| POST | `/api/v1/events` | Ingestar CSV |
| GET | `/api/v1/events` | Obtener eventos con filtros (environment, severity, status) |
| GET | `/api/v1/incidents` | Incidentes priorizados por severidad |
| POST | `/api/v1/predict` | Predicción fallo + severidad |
| POST | `/api/v1/explain` | Explicación SHAP + decision path |
| GET | `/api/v1/models` | Metadatos modelos entrenados |
| GET | `/api/v1/metrics` | Métricas Prometheus |

### Ejemplos:

```bash
# Predict
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"features": {"event_type": "LOG", "severity": "HIGH", "status": "FAILURE", "duration_ms": 5.0, "status_code": 500, "hour": 14}}'

# Explain
curl -X POST http://localhost:8000/api/v1/explain \
  -H "Content-Type: application/json" \
  -d '{"features": {"event_type": "LOG", "severity": "HIGH", "status": "FAILURE", "duration_ms": 5.0, "status_code": 500, "hour": 14}}'

# Metrics
curl http://localhost:8000/metrics
```

## 7. Flujo de trabajo CI/CD

```yaml
# .github/workflows/ci.yml
name: AIOps CI/CD

on: [push, pull_request]

jobs:
  lint: flake8 src/
  test: pytest tests/ -v
  security:
    - gitleaks/gitleaks-action
    - semgrep/semgrep-action
    - aquasecurity/trivy-action
  build: python -m src.ml.train
  deploy: render (conditional, main branch only)
```

### Stages:

1. **Lint**: flake8 en `src/`
2. **Test**: pytest, 10/10 tests pass
3. **Security**: gitleaks, semgrep, trivy scans
4. **Build**: entrena modelos, sube artifact
5. **Deploy**: a Render (branch main solo)

## 8. Configuración de Seguridad

### Gitleaks (.gitleaks.toml):

- Detecta API keys, strings de conexión DB, paths de modelos hardcodeados

### Semgrep (.semgrep.yml):

- Reglas Python: SQL injection, secrets codificados, weak RNG, path traversal

### Trivy (.trivy.yaml):

- Escaneos: vuln, secret, misconfig
- Ignora: .git, __pycache__, .venv, node_modules

### Depuración de seguridad:

```bash
# Gitleaks
gitleaks detect --source .

# Semgrep
semgrep scan --config .semgrep.yml .

# Trivy
trivy fs --exit-code 0 .
```

## 9. Observabilidad y Alerting

### Métricas Prometheus:

- `aioplog_api_requests_total` - contador total de peticiones
- `aioplog_api_request_duration_seconds` - histograma de duración

### Alertas OpenTelemetry (observability/alerts.yaml):

- **HighErrorRate**: tasa de errores > 10% por 5 min → crítico
- **HighLatency**: p95 latencia > 2s por 3 min → warning
- **HighPredictionFailureRate**: > 100 predicciones en 10 min → warning

### Dashboard (configurable):

- Grafana con datasource Prometheus
- Panels: request rate, error rate, latency percentiles, prediction volume

## 9b. Containerización con Docker

El proyecto incluye un `Dockerfile` que empaqueta la API FastAPI y un `docker-compose.yml`
que levanta la aplicación junto con PostgreSQL.

### Build de la imagen

```bash
docker build -t aiops-log-monitor .
```

### Run del contenedor (solo la app)

```bash
docker run -p 8000:8000 aiops-log-monitor
# Verificar:
curl http://localhost:8000/health
# Expected: {"status":"ok","timestamp":"..."}
```

> Nota: el contenedor necesita un modelo entrenado en `src/artifacts/`. Para generarlo
> dentro de la imagen localmente antes del build, ejecuta `python -m src.ml.train`, o
> entrena en tiempo de arranque personalizando el `CMD`.

### Stack completo con docker-compose (app + PostgreSQL)

```bash
docker compose up --build     # construye la app y levanta db + app
docker compose down           # detiene y elimina los contenedores
```

El servicio `app` espera a que `postgres` esté sano (`condition: service_healthy`)
antes de arrancar, y apunta `DATABASE_URL` al host `postgres` de la red interna.

## 10. Despliegue Automatizado

El proyecto está listo para desplegar en la nube con **Render** usando `render.yaml` (Blueprint de despliegue) y un `Dockerfile` comprometido en el repositorio.

### Código de despliegue (`render.yaml`)

```yaml
services:
  - type: web
    name: aiops-log-monitor
    runtime: docker
    dockerfilePath: ./Dockerfile
    healthCheckPath: /health
  - type: database
    name: aiops-db
    plan: free
    databaseName: aiops
    user: aiops
```

### Flujo de despliegue (Render)

1. Importar el repositorio como **Render Blueprint** (crea el servicio web + base de datos gestionada).
2. Añadir el secret `RENDER_DEPLOY_HOOK` en GitHub para que `deploy.yml` dispare releases.
3. Render construye la imagen Docker, ejecuta las migraciones y sirve la app.
4. Verificar que `/health` responde con `{"status":"ok"}` (código de estado 200).
5. (Opcional) Activar UptimeRobot cada 10 min para mantener el servicio Free Tier despierto.

### URL de testing (despliegue en la nube)

Una vez desplegado, el servicio expone un endpoint de salud:

```bash
curl https://<TU-SERVICIO>.onrender.com/health
# Expected: {"status":"ok","timestamp":"..."}
```

El marcador `<TU-SERVICIO>.onrender.com` se obtiene del dashboard de Render tras crear el Blueprint. Mientras se completa ese despliegue, la evidencia de funcionamiento local está en `docs/deployment/health_check.png` (respuesta real del endpoint `/health` y de `/api/v1/predict`):

```bash
# Ejemplo de respuesta real capturada:
{"status":"ok","timestamp":"2026-11-15T19:41:00.305609"}
```

### Free Tier (consideraciones)

- PostgreSQL gratuito expira después de 30 días.
- Servicio web duerme cuando está inactivo → cold start ~tens of seconds.
- Monitoreo con UptimeRobot cada 10 min (`/health`).

## 11. Licencia

MIT

## 12. Autor

N2026-2027 - AIOps Log Monitor Capstone Project

---

**Documentación relacionada**:

- `docs/ARCHITECTURE.md` — HLD completo
- `docs/LLD.md` — LLD con esquema SQL y endpoints
- `docs/API_CONTRACT.md` — contrato JSON de todos los endpoints
- `docs/SETUP.md` — guía paso a paso
- `observability/` — métricas, tracing, alerting
- `.github/workflows/ci.yml` — pipeline CI/CD

---
*Generado el 2026-11-13 como parte del Capstone Project AIOps Log Monitor.*