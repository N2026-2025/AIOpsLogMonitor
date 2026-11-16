# Capítulo 11: Plan de Testing (Chapter 11 - Testing Strategy)

## 1. Estrategia de pruebas

| Nivel | Tipo | Herramienta | Alcance | Frecuencia |
|-------|------|-------------|---------|------------|
| Unit | `pytest` | `tests/test_ingestion.py`, `tests/test_ml.py` | Ingestión, features, ML training, explicabilidad | Cada commit |
| API | `pytest` + FastAPI TestClient | `tests/test_api.py` | Health, predict, explain endpoints | Cada commit |
| E2E | `playwright` | `e2e/api.spec.ts` | API desde navegador (health, predict, explain, metrics, events) | Cada release |
| Security | `gitleaks`, `semgrep`, `trivy` | `.github/workflows/ci.yml` | Secretos, SQL injection, vulnerabilidades | Cada commit |
| Performance | `pytest` / manual | Benchmark predict | Latencia < 100ms por petición | Antes de release |
| Smoke | `curl` / manual | Endpoint `/health` | Servicio vivo | Post-deploy |

---

## 2. Unit Tests (`tests/`)

### test_ingestion.py (4 tests)
| Test | Descripción | RF | Estado |
|------|-------------|----|--------|
| test_basic_parsing | Ingestar CSV, verificar filas procesadas | RF-001 | ✅ PASS |
| test_feature_engineering | Generar features derivadas | RF-002 | ✅ PASS |
| test_sqlalchemy | Persistencia SQL, esquema | RF-007 | ✅ PASS |
| test_ml_training | Entrenar modelos, verificar métricas | RF-003, RF-004 | ✅ PASS |

### test_ml.py (3 tests)
| Test | Descripción | RF | Estado |
|------|-------------|----|--------|
| test_failure_prediction | Predecir fallo, accuracy 1.0 | RF-003 | ✅ PASS |
| test_anomaly_detection | Detección anomalía IsolationForest | RF-004 | ✅ PASS |
| test_explainability | SHAP values, decision path | RF-005 | ✅ PASS |

### test_api.py (3 tests)
| Test | Descripción | RF | Estado |
|------|-------------|----|--------|
| test_health | Healthcheck responde 200 | RF-006 | ✅ PASS |
| test_predict_endpoint | Predicción via API | RF-003, RF-006 | ✅ PASS |
| test_explain_endpoint | Explicación via API | RF-005, RF-006 | ✅ PASS |

**Resultado: 10/10 tests pass** en cada ejecución de `pytest tests/ -v`.

---

## 3. E2E Tests (`e2e/api.spec.ts`)

Playwright sugiere `npm run dev` para levantar la API localmente, luego ejecuta 5 tests:

| Test | Descripción | Estado |
|------|-------------|--------|
| health endpoint returns ok | GET /health | Ready |
| predict endpoint returns failure prediction | POST /api/v1/predict | Ready |
| explain endpoint returns SHAP values | POST /api/v1/explain | Ready |
| metrics endpoint exposes Prometheus format | GET /metrics | Ready |
| events endpoint returns list | GET /api/v1/events?limit=5 | Ready |

Comando: `npx playwright test` (requiere levantar `python -m src.api.main` primero)

---

## 4. CI/CD Pipeline (`.github/workflows/ci.yml`)

### Stages y jobs:

```yaml
lint:
  runs-on: ubuntu-latest
  steps:
    - flake8 src/ --max-line-length=120

test:  # needs lint
  runs-on: ubuntu-latest
  steps:
    - pip install -r requirements.txt
    - pytest tests/ -v

security:  # parallel
  runs-on: ubuntu-latest
  steps:
    - gitleaks detect --source .
    - semgrep scan --config .semgrep.yml .
    - trivy fs --exit-code 0 .

build:  # needs lint, test, security
  runs-on: ubuntu-latest
  steps:
    - python -m src.ml.train
    - upload artifact: aioplogmonitor_models_v0.1.0.pkl

deploy:  # needs build, main branch only
  runs-on: ubuntu-latest
  if: ref == 'refs/heads/main'
  steps:
    - render deploy (conditional)
```

**Condición de éxito**: Todos los jobs verdes → deploy automático a Render.

---

## 5. Security Tests

| Herramienta | Archivo config | Qué detecta | Umbral |
|-------------|----------------|-------------|--------|
| gitleaks | `.gitleaks.toml` | API keys, DB URLs, paths modelo hardcodeados | 0 hallazgos |
| semgrep | `.semgrep.yml` | SQL injection, secrets, weak RNG, path traversal | 0 hallazgos |
| trivy | `.trivy.yaml` | Vulnerabilidades, secrets, misconfig | HIGH/CRITICAL=0 |

---

## 6. Metrics de calidad

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Cobertura de tests | 100% features críticas | 10/10 pytest pass |
| Latencia predict | < 100ms | benchmark manual |
| Tasa fallo accuracy | 1.0 | test_failure_prediction |
| Errores 5xx en prod | < 10% | Prometheus alert |
| p95 latencia API | < 2s | Prometheus alert |
| Hallazgos críticos seguridad | 0 | gitleaks/semgrep/trivy |

---

## 7. Ejecución local

```bash
# Todos los tests
pytest tests/ -v

# Solo ingestion
pytest tests/test_ingestion.py -v

# Solo ML
pytest tests/test_ml.py -v

# Solo API
pytest tests/test_api.py -v

# Con Makefile
make test

# Lint
make lint
# o
flake8 src/ --max-line-length=120

# Security scan local
gitleaks detect --source .
semgrep scan --config .semgrep.yml .
trivy fs --exit-code 0 .
```

---

## 8. Riesgos y mitigaciones de testing

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| DB no disponible (PostgreSQL down) | Media | Alto | Graceful degradation en init_database |
| Modelo no entrenado | Baja | Alto | Endpoint retorna error 500 con mensaje |
| SHAP lento en features altas | Baja | Medio | TreeExplainer optimizado para RandomForest |
| Data drift en producción | Media | Medio | Re-entrenamiento periódico con nuevos datos |
| Cold start en free tier Render | Alta | Bajo | UptimeRobot ping cada 10 min |

---

## 9. Definición de "Done" para release

- [ ] `pytest tests/ -v` → 10/10 pass
- [ ] `flake8 src/ --max-line-length=120` → 0 warnings
- [ ] gitleaks detect → 0 hallazgos
- [ ] semgrep scan → 0 hallazgos críticos
- [ ] `python -m src.ml.train` → modelo entrenado, artifact en `src/artifacts/`
- [ ] `curl http://localhost:8000/health` → {"status":"ok"}
- [ ] `curl http://localhost:8000/metrics` → contiene `aioplog_api_requests_total`
- [ ] `make seed` → 200 eventos deterministas

---

## 10. Tabla de cobertura por requisito

| Requisito | Test | Estado | Evidencia |
|-----------|------|--------|-----------|
| RF-001 Ingestión CSV | test_basic_parsing | ✅ | tests/test_ingestion.py |
| RF-002 Feature Engineering | test_feature_engineering | ✅ | tests/test_ingestion.py |
| RF-003 Predicción fallos | test_failure_prediction | ✅ | tests/test_ml.py |
| RF-004 Anomalías | test_anomaly_detection | ✅ | tests/test_ml.py |
| RF-005 Explicación SHAP | test_explainability | ✅ | tests/test_ml.py |
| RF-006 API REST | test_health, test_predict, test_explain | ✅ | tests/test_api.py |
| RF-007 Almacenamiento SQL | test_sqlalchemy | ✅ | tests/test_ingestion.py |
| RF-009 Seed determinista | scripts/seed_deterministic.py | ✅ | 200 eventos, seed script |
| NFR-001 Rendimiento | benchmark predict | 🔲 | < 100ms objetivo |
| NFR-005 Observabilidad | /metrics endpoint | ✅ | prometheus format |