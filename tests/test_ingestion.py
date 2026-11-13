import sys
import os
import pandas as pd
import tempfile

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

# Get absolute path to data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
SAMPLE_CSV = os.path.join(DATA_DIR, 'sample.csv')

from src.ingestion.parse import EventParser, IngestionService, IngestionConfig
from src.ingestion.features import FeatureEngineer, FeaturePipeline, EventFeatures


def test_basic_parsing():
    """Test basic CSV parsing."""
    parser = EventParser()
    config = IngestionConfig()
    service = IngestionService(config)
    
    # Leer el sample CSV desde el data dir
    if not os.path.exists(SAMPLE_CSV):
        print(f"Sample CSV not found at {SAMPLE_CSV}")
        return False
    
    try:
        df = service.ingest_file(SAMPLE_CSV)
        print(f"[OK] Successfully parsed {len(df)} records from {SAMPLE_CSV}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Shape: {df.shape}")
        
        # Verificar columnas criticas
        critical_cols = ['event_type', 'severity', 'status', 'hostname', 'instance_id']
        for col in critical_cols:
            if col in df.columns:
                print(f"  [OK] Column '{col}' present")
            else:
                print(f"  [FAIL] Column '{col}' MISSING")
        
        return True
    except Exception as e:
        print(f"[FAIL] Failed to parse CSV: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_feature_engineering():
    """Test feature engineering."""
    try:
        from src.ingestion.parse import EventParser, IngestionService, IngestionConfig
        
        parser = EventParser()
        config = IngestionConfig()
        service = IngestionService(config)
        
        df = service.ingest_file(SAMPLE_CSV)
        
        # Feature engineering
        feature_engineer = FeatureEngineer()
        df_processed, numeric_cols = feature_engineer.fit_transform(df)
        
        print(f"[OK] Feature engineering completed")
        print(f"  Original shape: {df.shape}")
        print(f"  Processed shape: {df_processed.shape}")
        print(f"  Numeric cols: {len(numeric_cols)}")
        
        # Verificar columnas nuevas
        new_cols = ['hour_sin', 'hour_cos', 'is_weekend', 'severity_level', 'status_failure', 'log_duration', 'risk_score']
        for col in new_cols:
            if col in df_processed.columns:
                print(f"  [OK] New feature '{col}' created")
            else:
                print(f"  [FAIL] Feature '{col}' missing")
        
        return True
    except Exception as e:
        print(f"[FAIL] Feature engineering failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sqlalchemy():
    """Test SQLAlchemy model import."""
    try:
        from src.storage.models import Event, Prediction, Base
        from sqlalchemy import create_engine
        import sqlalchemy
        
        # Crear engine en memoria
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        
        print(f"[OK] SQLAlchemy models created successfully")
        print(f"  Tables: {list(Base.metadata.tables.keys())}")
        
        # Verificar que tables existen
        tables = list(Base.metadata.tables.keys())
        assert 'events' in tables or 'events' in str(tables).lower()
        assert 'predictions' in tables or 'predictions' in str(tables).lower()
        
        print(f"[OK] Tables 'events' and 'predictions' verified")
        return True
    except Exception as e:
        print(f"[FAIL] SQLAlchemy test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ml_training():
    """Test ML training pipeline."""
    try:
        from src.ml.train import AioMLPipeline
        from src.ingestion.parse import EventParser, IngestionService, IngestionConfig
        
        parser = EventParser()
        config = IngestionConfig()
        service = IngestionService(config)
        
        df = service.ingest_file(SAMPLE_CSV)
        
        # Training
        ml = AioMLPipeline(random_state=42)
        result = ml.train(df)
        
        print(f"[OK] ML training completed")
        print(f"  Models trained: {result['models_trained']}")
        print(f"  Metrics: {result['metrics']}")
        
        # Test prediction
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
        print(f"  Failure prediction: {prediction}")
        
        # Test anomaly detection
        anomaly = ml.detect_anomaly(test_features)
        print(f"  Anomaly detection: {anomaly}")
        
        return True
    except Exception as e:
        print(f"[FAIL] ML training test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todos los tests."""
    print("=" * 60)
    print("AIOps Log Monitor - Project Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Basic Parsing", test_basic_parsing()))
    results.append(("Feature Engineering", test_feature_engineering()))
    results.append(("SQLAlchemy Models", test_sqlalchemy()))
    results.append(("ML Training", test_ml_training()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)