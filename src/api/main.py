from fastapi import FastAPI, Query, Body, Request
from fastapi.responses import JSONResponse, Response
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import os
import time
import pandas as pd
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Imports locales
from src.ml.train import AioMLPipeline
from src.ml.explain import AioExplainPipeline
from src.storage.db import get_engine, get_session_factory, init_database, close_session
from src.storage import models

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACTS_PATH = os.path.join(PROJECT_ROOT, 'src', 'artifacts', 'aioplogmonitor_models_v0.1.0.pkl')

app = FastAPI(
    title="AIOps Log Monitor API",
    description="API para ingestión, consulta y predicción de incidentes AIOps",
    version="0.1.0"
)

# Inicializar DB al arrancar (no bloquear el arranque si la DB no está disponible)
try:
    init_database()
except Exception as e:
    print(f"Warning: database initialization skipped: {e}")

# Metrics
REQUEST_COUNT = Counter(
    "aioplog_api_requests_total",
    "Total number of AIOps API requests",
    ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram(
    "aioplog_api_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"]
)


@app.middleware("http")
async def add_prometheus_metrics(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_DURATION.labels(method=request.method, endpoint=request.url.path).observe(duration)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    return response


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

class IngestRequest(BaseModel):
    """Request para ingestión de datos."""
    csv_file_path: str
    chunk_size: int = 10000

class PredictRequest(BaseModel):
    """Request para predicción de fallo."""
    features: dict

class ExplainRequest(BaseModel):
    """Request para explicación de predicción."""
    features: dict

@app.get("/health")
def health():
    """Healthcheck de la API."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/events")
def ingest_events(request: IngestRequest):
    """Ingerir eventos desde CSV."""
    try:
        from src.ingestion.parse import IngestionService
        from src.ingestion.features import FeatureEngineer
        
        service = IngestionService()
        df = service.ingest_file(request.csv_file_path)
        
        # Persistir a PostgreSQL
        SessionLocal = get_session_factory()
        session = SessionLocal()
        
        storage_service = StorageService()
        stored_count = storage_service.store_events(session, df)
        
        session.close()
        
        return JSONResponse({
            "status": "success",
            "message": f"Stored {stored_count} events",
            "csv_file_path": request.csv_file_path,
            "chunk_size": request.chunk_size,
            "shape": [len(df), len(df.columns)]
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/api/v1/events")
def get_events(
    environment: Optional[str] = Query(None, description="Filtrar por entorno"),
    severity: Optional[str] = Query(None, description="Filtrar por severidad (LOW/MEDIUM/HIGH)"),
    status: Optional[str] = Query(None, description="Filtrar por status (SUCCESS/FAILURE)"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de resultados")
):
    """Obtener eventos con filtros."""
    try:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        
        storage_service = StorageService()
        events = storage_service.get_events(session, environment=environment, severity=severity, status=status, limit=limit)
        
        session.close()
        
        result = [event.to_dict() for event in events]
        
        return JSONResponse({
            "status": "success",
            "count": len(result),
            "events": result
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/api/v1/incidents")
def get_incidents(
    min_severity: str = Query("HIGH", description="Severidad mínima: LOW/MEDIUM/HIGH"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de resultados")
):
    """Obtener incidentes priorizados por severidad."""
    try:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        
        storage_service = StorageService()
        incidents = storage_service.get_incidents(session, min_severity=min_severity, limit=limit)
        
        session.close()
        
        result = [incident.to_dict() for incident in incidents]
        
        return JSONResponse({
            "status": "success",
            "count": len(result),
            "incidents": result,
            "min_severity": min_severity
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/v1/predict")
def predict(request: PredictRequest):
    """Predecir fallo y severidad dados features."""
    try:
        from src.ml.train import AioMLPipeline
        ml = AioMLPipeline()
        
        # Cargar artefactos si existen
        if os.path.exists(ARTIFACTS_PATH):
            import joblib
            artifacts = joblib.load(ARTIFACTS_PATH)
            ml.failure_model = artifacts['failure_model']
            ml.severity_model = artifacts['severity_model']
            ml.anomaly_model = artifacts['anomaly_model']
            ml.severity_encoder = artifacts['severity_encoder']
            ml.feature_cols = artifacts.get('feature_cols')
            ml.anomaly_cols = artifacts.get('anomaly_cols', ml.anomaly_cols)
            ml.models_trained = True
        
        # Predictor
        failure_pred = ml.predict_failure(request.features)
        severity_pred = ml.predict_severity(request.features)
        
        return JSONResponse({
            "status": "success",
            "features": request.features,
            "failure_prediction": failure_pred,
            "severity_prediction": severity_pred,
            "model_version": ml.model_version
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/v1/explain")
def explain(request: ExplainRequest):
    """Generar explicación SHAP y camino de árbol para predicción."""
    try:
        from src.ml.explain import AioExplainPipeline
        
        explain_pipeline = AioExplainPipeline()
        result = explain_pipeline.explain_prediction(request.features)
        
        return JSONResponse({
            "status": "success",
            "explanation": result,
            "features": request.features
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/api/v1/models")
def get_models():
    """Obtener metadatos de modelos."""
    try:
        import joblib
        
        if os.path.exists(ARTIFACTS_PATH):
            artifacts = joblib.load(ARTIFACTS_PATH)
            
            return JSONResponse({
                "status": "success",
                "model_version": artifacts['model_version'],
                "failure_model_type": type(artifacts['failure_model']).__name__,
                "severity_model_type": type(artifacts['severity_model']).__name__,
                "anomaly_model_type": type(artifacts['anomaly_model']).__name__,
                "feature_columns": artifacts['feature_cols']
            })
        else:
            return JSONResponse({"status": "error", "message": "No trained models found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# Importar después de definir handlers para evitar ciclos
from src.storage.init import StorageService


def main():
    """Entry point para uvicorn."""
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()