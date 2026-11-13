# API Contract — AIOps Log Monitor

Esquema de petición y respuesta firmado para el `src/api/main.py`. Todos los endpoints retornan JSON con un campo `status` (`success` | `error`).

## 1. `/health` (GET)

- **Respuesta 200:** `{ "status": "ok", "timestamp": "ISO8601" }`
- **Descripción:** indicador de vida (liveness).

## 2. `/api/v1/events` (POST)

- **Cuerpo (`IngestRequest`):**
  ```json
  {"csv_file_path": "/data/sample.csv", "chunk_size": 10000}
  ```
- **Respuesta 200 (`success`):**
  ```json
  {
    "status": "success",
    "message": "Stored 1000 events",
    "csv_file_path": "/data/sample.csv",
    "chunk_size": 10000,
    "shape": [1000, 34]
  }
  ```
- **Respuesta 500 (`error`):** `{ "status": "error", "message": "..." }`

## 3. `/api/v1/events` (GET) — listado filtrado

- **Query params:** `environment` (string), `severity` (LOW/MEDIUM/HIGH), `status` (SUCCESS/FAILURE), `limit` (1..1000, default 100).
- **Respuesta 200:** `{ "status": "success", "count": N, "events": [ ... to_dict() ...] }`

## 4. `/api/v1/incidents` (GET)

- **Query params:** `min_severity` (default HIGH), `limit` (default 100).
- **Respuesta 200:** `{ "status": "success", "count": N, "incidents": [...], "min_severity": "HIGH" }` — solo incidentes con `status_failure = true`, ordenados por `risk_score` descendente.

## 5. `/api/v1/predict` (POST)

- **Cuerpo (`PredictRequest`):** `{ "features": { ... } }`
- **Features esperadas:** `event_type`, `severity`, `status`, `duration_ms`, `status_code`, `hour`, `path`, `method`.
- **Respuesta 200:** `{ "status": "success", "features": {...}, "failure_prediction": bool, "severity_prediction": str, "model_version": "0.1.0" }`
- **Notas:** carga los artefactos desde `src/artifacts/aioplogmonitor_models_v0.1.0.pkl` si existen.

## 6. `/api/v1/explain` (POST)

- **Cuerpo (`ExplainRequest`):** `{ "features": { ... } }`
- **Respuesta 200 (`success`):**
  ```json
  {
    "status": "success",
    "explanation": {
      "features": {...},
      "shap_values": [number, ...],
      "top_contributing": [{ "feature": "severity", "value": 2, "shap": 0.8 }, ...],
      "decision_path": "@0: status_failure <= 0.5 -> True branch -> ...",
      "model_version": "0.1.0",
      "feature_importance": { "severity": 0.35, ... },
      "success": true
    },
    "features": {...}
  }
  ```

## 7. `/api/v1/models` (GET)

- **Respuesta 200 (`success`):** `{ "status": "success", "model_version": "0.1.0", "failure_model_type": "RandomForestClassifier", "severity_model_type": "RandomForestClassifier", "anomaly_model_type": "IsolationForest", "feature_columns": [...] }`
- **Respuesta 404 (`error`):** `{ "status": "error", "message": "No trained models found" }`
