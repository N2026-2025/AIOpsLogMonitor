import os
import sys
import pandas as pd
import numpy as np

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

# Get absolute path to data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
SAMPLE_CSV = os.path.join(DATA_DIR, 'sample.csv')

from src.ml.train import AioMLPipeline
from src.ml.explain import AioExplainPipeline


def test_failure_prediction():
    """Test failure prediction model."""
    from src.ingestion.parse import IngestionService, IngestionConfig

    service = IngestionService(IngestionConfig())
    df = service.ingest_file(SAMPLE_CSV)

    ml = AioMLPipeline(random_state=42)
    result = ml.train(df)

    success_features = {
        'event_type': 'INCOMING_REQUEST',
        'severity': 'LOW',
        'status': 'SUCCESS',
        'duration_ms': 10.0,
        'status_code': 200,
        'hour': 14,
        'path': '/api/v1/users',
        'method': 'GET',
    }

    success_pred = ml.predict_failure(success_features)
    assert success_pred['failure'] is False
    assert 0.0 <= success_pred['confidence'] <= 1.0

    failure_features = {
        'event_type': 'LOG',
        'severity': 'HIGH',
        'status': 'FAILURE',
        'duration_ms': 5.0,
        'status_code': 500,
        'hour': 14,
        'path': '/api/v1/users',
        'method': 'GET',
    }

    failure_pred = ml.predict_failure(failure_features)
    assert failure_pred['failure'] is True
    assert 0.0 <= failure_pred['confidence'] <= 1.0


def test_anomaly_detection():
    """Test anomaly detection."""
    from src.ingestion.parse import IngestionService, IngestionConfig

    service = IngestionService(IngestionConfig())
    df = service.ingest_file(SAMPLE_CSV)

    ml = AioMLPipeline(random_state=42)
    result = ml.train(df)

    test_features = {
        'event_type': 'INCOMING_REQUEST',
        'severity': 'MEDIUM',
        'status': 'SUCCESS',
        'duration_ms': 1200.0,
        'status_code': 200,
        'hour': 14,
        'path': '/performance/slow',
        'method': 'GET',
    }

    anomaly = ml.detect_anomaly(test_features)
    assert 'is_anomaly' in anomaly
    assert 'anomaly_score' in anomaly
    assert isinstance(anomaly['is_anomaly'], bool)


def test_explainability():
    """Test explainability pipeline."""
    explain = AioExplainPipeline()
    result = explain.explain_prediction({
        'event_type': 'LOG',
        'severity': 'HIGH',
        'status': 'FAILURE',
        'duration_ms': 2.5,
        'status_code': 500,
        'hour': 14,
    })

    assert result['success'] is True
    assert 'shap_values' in result
    assert 'top_contributing' in result
    assert 'decision_path' in result
    assert 'feature_importance' in result