import os
import sys
import pytest
from fastapi.testclient import TestClient
import pandas as pd

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

# Mock database with SQLite in-memory for testing
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'


def test_health():
    """Test health endpoint."""
    from src.api.main import app
    
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print(f"[OK] Health endpoint: {data}")


def test_predict_endpoint():
    """Test prediction endpoint."""
    from src.api.main import app
    from src.ml.train import AioMLPipeline
    from src.ingestion.parse import IngestionService, IngestionConfig
    
    # Train a quick model first
    service = IngestionService(IngestionConfig())
    
    # Get sample path
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    sample_csv = os.path.join(data_dir, 'sample.csv')
    
    df = service.ingest_file(sample_csv)
    ml = AioMLPipeline()
    ml.train(df)
    
    client = TestClient(app)
    
    features = {
        'event_type': 'LOG',
        'severity': 'HIGH',
        'status': 'FAILURE',
        'duration_ms': 5.0,
        'status_code': 500,
        'hour': 14,
    }
    
    response = client.post("/api/v1/predict", json={"features": features})
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"[OK] Prediction endpoint: {data}")


def test_explain_endpoint():
    """Test explain endpoint."""
    from src.api.main import app
    from src.ml.train import AioMLPipeline
    from src.ingestion.parse import IngestionService, IngestionConfig
    
    # Train a quick model first
    service = IngestionService(IngestionConfig())
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    sample_csv = os.path.join(data_dir, 'sample.csv')
    
    df = service.ingest_file(sample_csv)
    ml = AioMLPipeline()
    ml.train(df)
    
    client = TestClient(app)
    
    features = {
        'event_type': 'LOG',
        'severity': 'HIGH',
        'status': 'FAILURE',
        'duration_ms': 5.0,
        'status_code': 500,
        'hour': 14,
    }
    
    response = client.post("/api/v1/explain", json={"features": features})
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    explanation = data["explanation"]
    assert explanation["success"] is True
    assert "shap_values" in explanation
    assert "top_contributing" in explanation
    assert "decision_path" in explanation
    print(f"[OK] Explain endpoint: {data.get('status', 'unknown')}")


def main():
    """Run API tests."""
    print("=" * 60)
    print("AIOps Log Monitor - API Tests")
    print("=" * 60)
    
    results = []
    
    try:
        test_health()
        results.append(("Health", True))
    except Exception as e:
        print(f"[FAIL] Health test failed: {e}")
        results.append(("Health", False))
    
    try:
        test_predict_endpoint()
        results.append(("Predict", True))
    except Exception as e:
        print(f"[FAIL] Predict test failed: {e}")
        results.append(("Predict", False))
    
    try:
        test_explain_endpoint()
        results.append(("Explain", True))
    except Exception as e:
        print(f"[FAIL] Explain test failed: {e}")
        results.append(("Explain", False))
    
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