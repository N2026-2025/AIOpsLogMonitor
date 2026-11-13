import pandas as pd
import numpy as np
import shap
import os
from typing import Dict, Any, Tuple, List

import joblib


class AioExplainPipeline:
    """Pipeline de explicabilidad para modelos AIOps."""
    
    def __init__(self, model_path: str = None):
        base_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(os.path.dirname(base_dir))
        self.model_path = model_path or os.path.join(
            project_root, 'artifacts', 'aioplogmonitor_models_v0.1.0.pkl'
        )
        self.failure_model = None
        self.severity_model = None
        self.anomaly_model = None
        self.feature_cols = None
        self.model_version = None
        self.artifacts_loaded = False
    
    def load_artifacts(self):
        """Cargar artefactos entrenados."""
        if os.path.exists(self.model_path):
            artifacts = joblib.load(self.model_path)
            self.failure_model = artifacts['failure_model']
            self.severity_model = artifacts['severity_model']
            self.anomaly_model = artifacts['anomaly_model']
            self.feature_cols = artifacts.get('feature_cols', [])
            self.model_version = artifacts.get('model_version', '0.1.0')
            self.artifacts_loaded = True
            print(f"Artifacts loaded from: {self.model_path}")
        else:
            print(f"No artifacts found at: {self.model_path}")
    
    def explain_prediction(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Explicar una prediccion con SHAP y arbol de decision."""
        if not self.artifacts_loaded:
            self.load_artifacts()
        
        if self.failure_model is None:
            return {'error': 'Model not loaded', 'success': False}
        
        import pandas as pd
        row = pd.DataFrame([features]).fillna(0)
        
        # Feature preprocessing
        row['log_duration'] = np.log1p(row.get('duration_ms', 0))
        row['status_code_is_error'] = (row.get('status_code', 0) >= 400).astype(int)
        row['hour_sin'] = np.sin(2 * np.pi * row.get('hour', 0) / 24)
        row['hour_cos'] = np.cos(2 * np.pi * row.get('hour', 0) / 24)
        
        severity_map = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        row['severity_level'] = row.get('severity', 'MEDIUM').map(severity_map).fillna(1)
        row['status_failure'] = (row.get('status', 'SUCCESS').str.lower() == 'failure').astype(int)
        row['is_weekend'] = 0
        
        # Filtrar columnas disponibles
        X_rf = row[[c for c in self.feature_cols if c in row.columns]].fillna(0)
        
        # Codificar categoricas
        for col in X_rf.columns:
            if X_rf[col].dtype == 'object':
                X_rf[col] = X_rf[col].astype('category').cat.codes
        
        # SHAP explanation
        explainer = shap.TreeExplainer(self.failure_model)
        shap_values = explainer.shap_values(X_rf)
        
        shap_arr = shap_values[0]
        if hasattr(shap_arr, 'tolist'):
            shap_arr = shap_arr.tolist()
        
        # Top 5 features contribuyendo al fallo
        top_indices = np.argsort(-np.abs(shap_arr))[:5]
        top_features = []
        
        feature_names = self.feature_cols if self.feature_cols else [
            'severity', 'status_failure', 'log_duration', 'status_code_is_error',
            'risk_score', 'duration_ms', 'hour_sin', 'is_weekend'
        ]
        
        for idx in top_indices:
            if idx < len(feature_names):
                direction = "favoring failure" if shap_arr[idx] > 0 else "favoring success"
                top_features.append(
                    f"{feature_names[idx]}: {shap_arr[idx]:.4f} ({direction})"
                )
        
        # Feature importance global
        importances = self.failure_model.feature_importances_
        feature_importance_dict = {
            feature_names[i]: float(importances[i])
            for i in range(min(len(feature_names), len(importances)))
        }
        
        # Decision path (explicacion simplificada)
        decision_path = self._decision_path_description(X_rf)
        
        return {
            'features': features,
            'shap_values': shap_arr,
            'top_contributing': top_features,
            'decision_path': decision_path,
            'model_version': self.model_version,
            'feature_importance': feature_importance_dict,
            'success': True,
        }
    
    def _decision_path_description(self, row: pd.DataFrame) -> str:
        """Generar descripcion del camino de decision del arbol."""
        try:
            tree = self.failure_model.estimators_[0]
            from sklearn.tree import _tree
            
            tree_ = tree.tree_
            path_nodes = []
            
            def recurse(node, depth):
                if tree_.feature[node] != _tree.TREE_UNDEFINED:
                    name = self.feature_cols[node] if self.feature_cols else f"feature_{node}"
                    threshold = tree_.threshold[node]
                    
                    val = row.iloc[0][name] if name in row.columns else np.nan
                    
                    if val <= threshold:
                        path_nodes.append(f"@{depth}: {name} <= {threshold:.2f} -> True branch")
                    else:
                        path_nodes.append(f"@{depth}: {name} > {threshold:.2f} -> False branch")
                    
                    recurse(tree_.children_left[node], depth + 1)
                    recurse(tree_.children_right[node], depth + 1)
                else:
                    path_nodes.append(f"@{depth}: Leaf node - prediction")
            
            recurse(0, 0)
            return " -> ".join(path_nodes) if path_nodes else "No path available"
        except Exception as e:
            return f"Decision path error: {e}"
    
    def get_global_explanation(self) -> Dict[str, Any]:
        """Obtener explicacion global de importancia de features."""
        if not self.artifacts_loaded or self.failure_model is None:
            return {'error': 'Model not loaded'}
        
        importances = self.failure_model.feature_importances_
        feature_names = self.feature_cols if self.feature_cols else []
        
        top_indices = np.argsort(-importances)[:5]
        top_features = [{'feature': feature_names[i], 'importance': float(importances[i])} for i in top_indices if i < len(feature_names)]
        
        bottom_indices = np.argsort(importances)[:3]
        bottom_features = [{'feature': feature_names[i], 'importance': float(importances[i])} for i in bottom_indices if i < len(feature_names)]
        
        return {
            'top_features': top_features,
            'bottom_features': bottom_features,
            'success': True,
        }


def main():
    """Punto de entrada CLI."""
    from src.ml.train import AioMLPipeline
    
    ml = AioMLPipeline()
    
    import pandas as pd
    df = pd.read_csv("data/sample.csv", nrows=100)
    result = ml.train(df)
    
    explain = AioExplainPipeline()
    explain_result = explain.explain_prediction({
        'event_type': 'LOG',
        'severity': 'HIGH',
        'status': 'FAILURE',
        'duration_ms': 2.5,
        'status_code': 500,
        'hour': 14,
    })
    
    return explain_result


if __name__ == "__main__":
    main()