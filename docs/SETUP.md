# Setup - Guía Rápida

## Requisitos

- Python 3.11+
- PostgreSQL 14+ (opcional para tests, se usa SQLite in-memory)
- Docker (opcional)

## Instalación

Recomendamos usar un entorno virtual aislado (`.venv`) para aislar las dependencias del proyecto del resto del sistema:

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# Windows (PowerShell / cmd):
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Instalar dependencias (con el entorno activo)
pip install -r requirements.txt
```

El archivo `requirements.txt` lista todas las dependencias. El entorno virtual se crea en la raíz del proyecto y se ignora con Git (`.venv/` está en `.gitignore`).

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
