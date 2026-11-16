# Capítulo 1: Requisitos Funcionales (Chapter 24.3 - Req-FR)

## Requisitos del producto y sistema

### RF-001: Ingestión de datos de logs
- **Descripción**: El sistema debe poder leer y procesar archivos CSV del AIOps Log Monitoring Dataset (1746 eventos).
- **Eventos mínimos**: 1746 eventos procesados con éxito.
- **Entradas**: `data/sample.csv` o `data/processed_events_analysis.csv`.
- **Salidas**: DataFrame pandas limpio con metadatos (`source_file`, `ingested_at`, `environment`, `instance_id`, `service_name`).

### RF-002: Feature Engineering
- **Descripción**: El sistema debe generar features derivadas para modelos ML.
- **Features derivadas**:
  - Temporal: `hour_sin`, `hour_cos`, `day_of_week_num`, `is_weekend`
  - Severidad: `severity_level` (LOW=0, MEDIUM=1, HIGH=2), `status_failure` (binario)
  - Riesgo: `log_duration` (log1p), `status_code_is_error`, `risk_score` (0.4*severity + 0.3*failure + 0.2*log_duration + 0.1*is_weekend)

### RF-003: Predicción de fallos y severidad
- **Descripción**: El modelo debe predecir si un evento representa un fallo y su gravedad.
- **Modelos**:
  - `RandomForestClassifier` (n_estimators=100) para fallo binario FAILURE/SUCCESS.
  - `RandomForestClassifier` (n_estimators=100) para severidad multiclase LOW/MEDIUM/HIGH.
- **Métricas esperadas**: accuracy fallo = 1.0 (sobre conjunto de test 80/20).

### RF-004: Detección de anomalías
- **Descripción**: El modelo debe detectar anomalías de latencia usando IsolationForest.
- **Características**: `contamination=0.1`, features: `log_duration`, `status_code`, `duration_ms`.
- **Salida**: `is_anomaly` (bool), `anomaly_score` (float decision_function).

### RF-005: Explicación SHAP y caminos de árbol
- **Descripción**: El sistema debe generar explicaciones interpretables para cada predicción.
- **Explicaciones**:
  - SHAP values (valores SHAP para cada feature en la predicción).
  - Decision path (árbol de decisión del primer árbol, ruta completa desde raíz hasta hoja).
  - Feature importance global (importancia de features a nivel global).

### RF-006: API REST FastAPI
- **Endpoints requeridos**:
  - `GET /health` — healthcheck `{"status": "ok", "timestamp": "..."}`.
  - `POST /api/v1/predict` — predicción fallo + severidad dados features JSON.
  - `POST /api/v1/explain` — explicación SHAP + decision path.
  - `GET /api/v1/events` — listado de eventos con filtros (environment, severity, status, limit).
  - `GET /api/v1/incidents` — incidentes priorizados por severidad mínima.
  - `GET /api/v1/metrics` — métricas Prometheus (formato `/metrics`).
  - `GET /api/v1/models` — metadatos modelo (version, tipos, feature_cols).

### RF-007: Almacenamiento en PostgreSQL
- **Descripción**: El sistema debe persistir eventos y predicciones en base de datos SQL.
- **Tablas**:
  - `Event`: 30+ columnas (timestamp, event_type, severity, status, duration_ms, status_code, environment, instance_id, service_name, risk_score, is_weekend, severity_level, status_failure, log_duration, status_code_is_error, etc.).
  - `Prediction`: foreign key a Event, modelo_version, failure_prediction, severity_prediction, anomaly_score.

### RF-008: Ingestión por lotes (chunking)
- **Descripción**: El pipeline de ingesta debe soportar procesamiento por lotes para archivos grandes.
- **Chunk size**: configurable (default 10000 filas por lote).
- **Batch size**: configurable (default 1000 filas por inserción).

### RF-009: Seed determinista
- **Descripción**: El sistema debe poder generar un dataset semillla fijo para CI/CD, tests y demos.
- **Script**: `scripts/seed_deterministic.py` con `np.random.seed(42)`.
- **Salida**: `data/seed_deterministic.csv` con 200 eventos, 25% tasa de fallo, 5 entornos, 3 severidades.

### RF-010: Predicción en tiempo real
- **Descripción**: La API debe responder predicciones en milisegundos (< 100ms por petición).
- **Latencia objetivo**: < 100ms por `POST /api/v1/predict`.
- **Confidence**: probabilidad `float` en `predict_failure` via `predict_proba`.

---

### Tabla de cobertura de requisitos funcionales

| # | Requisito | Tipo | Endpoint / Módulo | Evidencia |
|---|-----------|------|-------------------|-----------|
| RF-001 | Ingestión CSV | Funcional | `src/ingestion/parse.py` | test_basic_parsing ✅ |
| RF-002 | Feature Engineering | Funcional | `src/ingestion/features.py` | test_feature_engineering ✅ |
| RF-003 | Predicción fallos | Funcional | `src/ml/train.py` + API `/api/v1/predict` | test_failure_prediction ✅ |
| RF-004 | Detección anomalías | Funcional | `src/ml/train.py` + IsolationForest | test_anomaly_detection ✅ |
| RF-005 | Explicación SHAP | Funcional | `src/ml/explain.py` + API `/api/v1/explain` | test_explainability ✅ |
| RF-006 | API REST FastAPI | Funcional | `src/api/main.py` | 7/7 endpoints testados ✅ |
| RF-007 | Almacenamiento SQL | Funcional | `src/storage/models.py`, `db.py` | test_sqlalchemy ✅ |
| RF-008 | Chunking ingestion | Funcional | `src/ingestion/parse.py` | IngestService(config) ✅ |
| RF-009 | Seed determinista | Funcional | `scripts/seed_deterministic.py` | seed script creado ✅ |
| RF-010 | Predicción RT | No-funcional | `src/api/main.py` middleware metrics | latency benchmark |