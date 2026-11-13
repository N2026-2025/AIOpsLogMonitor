import pandas as pd
import numpy as np
import os
from typing import Dict, Any
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import shap

from src.ingestion.features import FeatureEngineer

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AioMLPipeline:
    """Pipeline ML para AIOps: predicción de fallos, severidad y anomalías."""
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.failure_model = None
        self.severity_model = None
        self.anomaly_model = None
        self.models_trained = False
        self.model_version = "0.1.0"
        self.artifacts_dir = os.path.join(PROJECT_ROOT, 'artifacts')
        os.makedirs(self.artifacts_dir, exist_ok=True)
        self.feature_engineer = FeatureEngineer()
        self.feature_cols = None
        self.anomaly_cols = None
    
    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Entrenar todos los modelos."""
        # Aplicar ingenieria de features primero
        df_features, numeric_cols = self.feature_engineer.fit_transform(df)
        
        # Preparar datos
        X = df_features.copy()
        y_failure = (X.get('status', pd.Series(['SUCCESS'] * len(X))) == 'FAILURE').astype(int)
        y_severity = X.get('severity', pd.Series(['MEDIUM'] * len(X))).astype(str)
        
        # Seleccionar columnas disponibles para el modelo
        available_cols = [c for c in numeric_cols + [
            'event_type', 'category', 'severity', 'status', 'hostname', 'os',
            'logger_name', 'level', 'method', 'path', 'region', 'app_version',
            'day_of_week', 'duration_ms', 'status_code', 'hour', 'month', 'week',
            'line', 'process_id', 'event_count'
        ] if c in X.columns]
        
        # Filtrar solo columnas de tipo numerico para RF
        X_rf = X[available_cols].copy()
        X_rf = X_rf.fillna(0)
        
        # Codificar categoricas
        for col in X_rf.columns:
            if X_rf[col].dtype == 'object':
                X_rf[col] = X_rf[col].astype(str).astype('category').cat.codes
        
        self.feature_cols = available_cols

        # Usar los mismos indices de split para fallo y severidad
        indices = np.arange(len(X_rf))
        train_idx, test_idx = train_test_split(
            indices, test_size=0.2, random_state=self.random_state,
            stratify=y_failure if len(set(y_failure)) > 1 else None
        )

        X_train = X_rf.iloc[train_idx]
        X_test = X_rf.iloc[test_idx]
        y_train = y_failure.iloc[train_idx]
        y_test = y_failure.iloc[test_idx]
        y_sev_train = y_severity.iloc[train_idx]

        # Modelo de fallo (binario)
        self.failure_model = RandomForestClassifier(
            n_estimators=100, random_state=self.random_state, n_jobs=-1
        )
        self.failure_model.fit(X_train, y_train)

        # Modelo de severidad (multiclase)
        severity_encoder = LabelEncoder()
        severity_encoder.fit(y_severity)
        severity_model = RandomForestClassifier(
            n_estimators=100, random_state=self.random_state, n_jobs=-1
        )
        severity_model.fit(X_train, severity_encoder.transform(y_sev_train))
        self.severity_model = severity_model
        self.severity_encoder = severity_encoder
        
        # Modelo de anomalías Isolation Forest (sobre duracion)
        anomaly_model = IsolationForest(
            contamination=0.1, random_state=self.random_state, n_estimators=100
        )
        anomaly_cols = ['log_duration', 'status_code', 'duration_ms']
        available_anomaly_cols = [c for c in anomaly_cols if c in X_rf.columns]
        if not available_anomaly_cols:
            available_anomaly_cols = numeric_cols[:3]
        anomaly_model.fit(X_train[available_anomaly_cols])
        self.anomaly_model = anomaly_model
        self.anomaly_cols = available_anomaly_cols
        
        self.models_trained = True
        
        # Evaluar
        y_pred = self.failure_model.predict(X_test)
        metrics = {
            'failure_accuracy': float(accuracy_score(y_test, y_pred)),
            'failure_precision': float(precision_score(y_test, y_pred, zero_division=0)),
            'failure_recall': float(recall_score(y_test, y_pred, zero_division=0)),
            'failure_f1': float(f1_score(y_test, y_pred, zero_division=0)),
        }
        
        # Guardar modelos
        artifacts = {
            'failure_model': self.failure_model,
            'severity_model': self.severity_model,
            'anomaly_model': self.anomaly_model,
            'severity_encoder': self.severity_encoder,
            'anomaly_cols': self.anomaly_cols,
            'model_version': self.model_version,
            'feature_cols': self.feature_cols,
        }
        
        artifacts_path = os.path.join(
            self.artifacts_dir, f'aioplogmonitor_models_v{self.model_version}.pkl'
        )
        joblib.dump(artifacts, artifacts_path)
        
        print(f"Models trained successfully. Artifacts: {artifacts_path}")
        print(f"Metrics: {metrics}")
        
        return {'models_trained': self.models_trained, 'metrics': metrics}
    
    def _prepare_input(self, features: Dict[str, Any]) -> pd.DataFrame:
        """Preparar input para prediccion aplicando feature engineering."""
        import pandas as pd
        row = pd.DataFrame([features])
        row = row.fillna(0)
        
        # Aplicar mismo feature engineering
        row['hour_sin'] = np.sin(2 * np.pi * row['hour'] / 24) if 'hour' in row.columns else 0
        row['hour_cos'] = np.cos(2 * np.pi * row['hour'] / 24) if 'hour' in row.columns else 0
        
        severity_map = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        row['severity_level'] = row.get('severity', 'MEDIUM').map(severity_map).fillna(1)
        row['status_failure'] = (row.get('status', 'SUCCESS').str.lower() == 'failure').astype(int)
        
        row['log_duration'] = np.log1p(row.get('duration_ms', 0).fillna(0))
        row['status_code_is_error'] = (row.get('status_code', 0) >= 400).astype(int)
        
        log_max = row.get('log_duration', 1).max()
        row['risk_score'] = (
            row.get('severity_level', 1) * 0.4 +
            row.get('status_failure', 0) * 0.3 +
            row.get('log_duration', 0) / log_max * 0.2 if log_max > 0 else 0 +
            row.get('is_weekend', 0) * 0.1
        )
        
        # Codificar categoricas igual que en train
        for col in row.columns:
            if row[col].dtype == 'object':
                row[col] = row[col].astype(str)
        
        return row
    
    def _align_features(self, row: pd.DataFrame) -> pd.DataFrame:
        """Alinear filas al orden de features usado en entrenamiento, rellenando faltantes con 0."""
        X = pd.DataFrame(index=row.index)
        for col in self.feature_cols:
            if col in row.columns:
                X[col] = row[col]
            else:
                X[col] = 0
        # Codificar categoricas igual que en train
        for col in X.columns:
            if X[col].dtype == 'object':
                X[col] = X[col].astype('category').cat.codes
        return X.fillna(0)

    def predict_failure(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predecir fallo dado features."""
        if not self.models_trained:
            raise ValueError("Model not trained. Call train first.")
        
        row = self._prepare_input(features)
        X_rf = self._align_features(row)
        
        prediction = int(self.failure_model.predict(X_rf)[0])
        probability = float(self.failure_model.predict_proba(X_rf)[0][1])
        
        return {
            'failure': bool(prediction),
            'confidence': probability,
            'features': features,
        }
    
    def predict_severity(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predecir severidad dada features."""
        if not self.models_trained:
            raise ValueError("Model not trained. Call train first.")
        
        row = self._prepare_input(features)
        X_rf = self._align_features(row)
        
        severity = self.severity_model.predict(X_rf)[0]
        severity_str = self.severity_encoder.inverse_transform([severity])[0]
        return {'severity': str(severity_str), 'success': True}
    
    def detect_anomaly(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Detectar anomalía de latencia dada features."""
        if not self.models_trained:
            raise ValueError("Model not trained. Call train first.")
        
        row = self._prepare_input(features)
        X_anomaly = row[[c for c in self.anomaly_cols if c in row.columns]].fillna(0)

        score = float(self.anomaly_model.decision_function(X_anomaly)[0])
        prediction = int(self.anomaly_model.predict(X_anomaly)[0])
        is_anomaly = prediction == -1
        
        return {
            'is_anomaly': bool(is_anomaly),
            'anomaly_score': score,
            'features': features,
        }
    
    def explain_failure(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Generar explicacion SHAP y camino de arbol para fallo."""
        if not self.models_trained:
            raise ValueError("Model not trained. Call train first.")
        
        import pandas as pd
        row = self._prepare_input(features)
        X_rf = self._align_features(row)
        
        explainer = shap.TreeExplainer(self.failure_model)
        shap_values = explainer.shap_values(X_rf)
        
        return {
            'features': features,
            'shap_values': shap_values[0].tolist() if hasattr(shap_values[0], 'tolist') else shap_values[0],
            'explanation': f"Analisis SHAP para evento con status={features.get('status')}, severidad={features.get('severity')}",
            'feature_importance': self._get_feature_importance(),
            'success': True,
        }
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Obtener feature importance."""
        if self.failure_model is None:
            return {}
        
        importances = self.failure_model.feature_importances_
        feature_names = self.feature_cols if self.feature_cols else []
        
        return {name: float(imp) for name, imp in zip(feature_names, importances)}


def main():
    """Punto de entrada principal para CLI de entrenamiento."""
    from src.ingestion.parse import IngestionService, IngestionConfig
    
    service = IngestionService(IngestionConfig())
    df = service.ingest_file("data/sample.csv")
    
    pipeline = AioMLPipeline()
    result = pipeline.train(df)
    
    return result


if __name__ == "__main__":
    main()