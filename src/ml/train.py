import pandas as pd
import numpy as np
import os
from typing import Dict, Any
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, make_scorer
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
        available_cols = list(dict.fromkeys(available_cols))
        
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

        # Modelo de fallo (binario) con tuning de hiperparametros
        failure_param_grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 10, 20],
            "min_samples_leaf": [1, 3, 5],
        }
        failure_search = RandomizedSearchCV(
            RandomForestClassifier(random_state=self.random_state, n_jobs=-1),
            param_distributions=failure_param_grid,
            n_iter=8,
            cv=3,
            scoring="f1",
            random_state=self.random_state,
            n_jobs=-1,
            verbose=0,
        )
        failure_search.fit(X_train, y_train)
        self.failure_model = failure_search.best_estimator_
        self.failure_best_params = failure_search.best_params_
        print(f"Failure model best params: {self.failure_best_params}")

        # Modelo de severidad (multiclase) con tuning
        severity_encoder = LabelEncoder()
        severity_encoder.fit(y_severity)
        severity_param_grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 10, 20],
        }
        severity_search = RandomizedSearchCV(
            RandomForestClassifier(random_state=self.random_state, n_jobs=-1),
            param_distributions=severity_param_grid,
            n_iter=6,
            cv=3,
            scoring="f1_macro",
            random_state=self.random_state,
            n_jobs=-1,
            verbose=0,
        )
        severity_search.fit(X_train, severity_encoder.transform(y_sev_train))
        severity_model = severity_search.best_estimator_
        self.severity_best_params = severity_search.best_params_
        print(f"Severity model best params: {self.severity_best_params}")
        self.severity_model = severity_model
        self.severity_encoder = severity_encoder

        # Modelo de anomalias Isolation Forest con tuning
        anomaly_cols = ['log_duration', 'status_code', 'duration_ms']
        available_anomaly_cols = [c for c in anomaly_cols if c in X_rf.columns]
        if not available_anomaly_cols:
            available_anomaly_cols = numeric_cols[:3]

        def _anomaly_scorer(estimator, X, y=None):
            # IsolationForest es no supervisado: puntuamos con score_samples
            return float(np.mean(estimator.score_samples(X)))

        anomaly_param_grid = {
            "contamination": [0.05, 0.1, 0.2, 0.3],
            "n_estimators": [50, 100, 200],
            "max_samples": [0.5, 1.0],
        }
        anomaly_search = RandomizedSearchCV(
            IsolationForest(random_state=self.random_state),
            param_distributions=anomaly_param_grid,
            n_iter=6,
            cv=3,
            scoring=_anomaly_scorer,
            random_state=self.random_state,
            n_jobs=1,
            verbose=0,
        )
        anomaly_search.fit(X_train[available_anomaly_cols])
        self.anomaly_model = anomaly_search.best_estimator_
        self.anomaly_best_params = anomaly_search.best_params_
        print(f"Anomaly model best params: {self.anomaly_best_params}")
        self.anomaly_cols = available_anomaly_cols

        self.models_trained = True

        # Evaluar
        y_pred = self.failure_model.predict(X_test)
        metrics = {
            "failure_accuracy": float(accuracy_score(y_test, y_pred)),
            "failure_precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "failure_recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "failure_f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "failure_best_params": self.failure_best_params,
            "severity_best_params": self.severity_best_params,
            "anomaly_best_params": self.anomaly_best_params,
        }

        # Guardar modelos
        artifacts = {
            "failure_model": self.failure_model,
            "severity_model": self.severity_model,
            "anomaly_model": self.anomaly_model,
            "severity_encoder": self.severity_encoder,
            "anomaly_cols": self.anomaly_cols,
            "model_version": self.model_version,
            "feature_cols": self.feature_cols,
            "failure_best_params": self.failure_best_params,
            "severity_best_params": self.severity_best_params,
            "anomaly_best_params": self.anomaly_best_params,
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
        row = pd.DataFrame([features])
        row = row.fillna(0)

        row['hour'] = row['hour'].astype(float) if 'hour' in row.columns else 0
        row['hour_sin'] = np.sin(2 * np.pi * row['hour'] / 24)
        row['hour_cos'] = np.cos(2 * np.pi * row['hour'] / 24)

        severity_map = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        row['severity'] = row['severity'].astype(str) if 'severity' in row.columns else 'MEDIUM'
        row['severity_level'] = row['severity'].map(severity_map).fillna(1).astype(float)

        row['status'] = row['status'].astype(str) if 'status' in row.columns else 'SUCCESS'
        row['status_failure'] = row['status'].str.lower().eq('failure').astype(int)

        row['duration_ms'] = row['duration_ms'].astype(float) if 'duration_ms' in row.columns else 0
        row['status_code'] = row['status_code'].astype(float) if 'status_code' in row.columns else 0
        row['log_duration'] = np.log1p(row['duration_ms'])
        row['status_code_is_error'] = (row['status_code'] >= 400).astype(int)
        row['is_weekend'] = row['is_weekend'].astype(int) if 'is_weekend' in row.columns else 0

        log_max = float(row['log_duration'].max())
        row['risk_score'] = (
            row['severity_level'] * 0.4
            + row['status_failure'] * 0.3
            + (row['log_duration'] / log_max * 0.2 if log_max > 0 else 0)
            + row['is_weekend'] * 0.1
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