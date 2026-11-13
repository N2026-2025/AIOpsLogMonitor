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


def test_failure_prediction():
    """Test failure prediction model."""
    try:
        from src.ingestion.parse import IngestionService, IngestionConfig
        
        service = IngestionService(IngestionConfig())
        df = service.ingest_file(SAMPLE_CSV)
        
        ml = AioMLPipeline(random_state=42)
        result = ml.train(df)
        
        # Test successful prediction
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
        print(f"  [SUCCESS] Success prediction: {success_pred}")
        
        # Test failure prediction
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
        print(f"  [SUCCESS] Failure prediction: {failure_pred}")
        
        # Both should run successfully
        return True
    except Exception as e:
        print(f"[FAIL] Failure prediction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_anomaly_detection():
    """Test anomaly detection."""
    try:
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
        print(f"  [SUCCESS] Anomaly detection: {anomaly}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Anomaly detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_explainability():
    """Test explainability pipeline."""
    try:
        from src.ml.explain import AioExplainPipeline
        
        explain = AioExplainPipeline()
        result = explain.explain_prediction({
            'event_type': 'LOG',
            'severity': 'HIGH',
            'status': 'FAILURE',
            'duration_ms': 2.5,
            'status_code': 500,
            'hour': 14,
        })
        
        print(f"  [SUCCESS] Explainability: {result}")
        
        # Should have explanation
        if not result.get('success', True):
            return False
        
        if 'explanation' not in result or 'shap_values' not in result:
            print("  [WARN] Missing explanation fields")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Explainability test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all ML tests."""
    print("=" * 60)
    print("AIOps Log Monitor - ML Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Failure Prediction", test_failure_prediction()))
    results.append(("Anomaly Detection", test_anomaly_detection()))
    results.append(("Explainability", test_explainability()))
    
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
