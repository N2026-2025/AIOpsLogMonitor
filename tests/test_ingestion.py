import sys
import os
import pandas as pd

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

# Get absolute path to data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
SAMPLE_CSV = os.path.join(DATA_DIR, 'sample.csv')

from src.ingestion.parse import EventParser, IngestionService, IngestionConfig  # noqa: E402
from src.ingestion.features import FeatureEngineer  # noqa: E402


def test_basic_parsing():
    """Test basic CSV parsing."""
    assert os.path.exists(SAMPLE_CSV), f"Sample CSV not found at {SAMPLE_CSV}"

    service = IngestionService(IngestionConfig())
    df = service.ingest_file(SAMPLE_CSV)

    assert len(df) > 0, "DataFrame vacío"
    critical_cols = ['event_type', 'severity', 'status', 'hostname', 'instance_id']
    for col in critical_cols:
        assert col in df.columns, f"Column '{col}' MISSING"


def test_feature_engineering():
    """Test feature engineering."""
    assert os.path.exists(SAMPLE_CSV), f"Sample CSV not found at {SAMPLE_CSV}"

    service = IngestionService(IngestionConfig())
    df = service.ingest_file(SAMPLE_CSV)

    feature_engineer = FeatureEngineer()
    df_processed, numeric_cols = feature_engineer.fit_transform(df)

    assert len(numeric_cols) > 0
    new_cols = [
        'hour_sin', 'hour_cos', 'is_weekend', 'severity_level',
        'status_failure', 'log_duration', 'risk_score'
    ]
    for col in new_cols:
        assert col in df_processed.columns, f"Feature '{col}' missing"
    assert df_processed.shape[0] == df.shape[0]


def test_sqlalchemy():
    """Test SQLAlchemy model import."""
    from src.storage.models import Event, Prediction, Base
    from sqlalchemy import create_engine

    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)

    tables = list(Base.metadata.tables.keys())
    assert 'events' in tables
    assert 'predictions' in tables


def test_ml_training():
    """Test ML training pipeline."""
    from src.ml.train import AioMLPipeline

    service = IngestionService(IngestionConfig())
    df = service.ingest_file(SAMPLE_CSV)

    ml = AioMLPipeline(random_state=42)
    result = ml.train(df)

    assert result['models_trained'] is True
    assert 'failure_accuracy' in result['metrics']

    test_features = {
        'event_type': 'LOG',
        'severity': 'HIGH',
        'status': 'FAILURE',
        'duration_ms': 5.0,
        'status_code': 500,
        'hour': 14,
        'path': '/api/v1/users',
        'method': 'GET',
    }

    prediction = ml.predict_failure(test_features)
    assert prediction['failure'] is True
    assert 0.0 <= prediction['confidence'] <= 1.0

    anomaly = ml.detect_anomaly(test_features)
    assert 'is_anomaly' in anomaly
