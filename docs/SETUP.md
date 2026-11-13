# Setup - Guía Rápida

## Requisitos

- Python 3.11+
- PostgreSQL 14+ (opcional para tests, se usa SQLite in-memory)
- Docker (opcional)

## Instalación

```bash
git clone <repo-aiops>
cd AIOpsLogMonitor
pip install -r requirements.txt
```

## Configuración

```bash
# Variables de entorno
export DATABASE_URL="postgresql://aion:aion@localhost:5432/aion"
export AIOPS_MODEL_PATH="src/artifacts/aioplogmonitor_models_v0.1.0.pkl"
export AIOPS_CSV_PATH="data/sample.csv"
```

## Pasos

1. **Iniciar PostgreSQL**
   ```bash
   docker compose up -d postgres
   python -m src.storage.init init
   ```

2. **Ingerir datos**
   ```bash
   python -m src.ingestion.parse data/sample.csv
   ```

3. **Entrenar modelos**
   ```bash
   python -m src.ml.train
   ```

4. **Iniciar API**
   ```bash
   python -m src.api.main
   # o
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   ```

5. **Probar**
   ```bash
   # Health
   curl http://localhost:8000/health
   
   # Predict
   curl -X POST http://localhost:8000/api/v1/predict \
     -H "Content-Type: application/json" \
     -d '{"features": {"event_type": "LOG", "severity": "HIGH", "status": "FAILURE", "duration_ms": 5.0, "status_code": 500, "hour": 14}}'
   ```

## Tests

```bash
pytest tests/ -v
```
