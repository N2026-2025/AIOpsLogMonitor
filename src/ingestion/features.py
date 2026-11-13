from typing import Dict, Any, Tuple
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import numpy as np
import pandas as pd

class FeatureEngineer:
    """Feature engineering para modelado AIOps."""
    
    def __init__(self):
        self.categorical_features = [
            'event_type', 'category', 'severity', 'status', 'hostname', 'os', 
            'logger_name', 'level', 'method', 'path', 'region', 'app_version'
        ]
        self.numeric_features = [
            'duration_ms', 'status_code', 'hour', 'month', 'week', 'line', 
            'process_id', 'event_count'
        ]
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_names = None
    
    def fit_transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
        """Crear features para ML."""
        df_processed = df.copy()
        
        # Features de tiempo/patrón
        df_processed['hour_sin'] = np.sin(2 * np.pi * df_processed['hour'] / 24)
        df_processed['hour_cos'] = np.cos(2 * np.pi * df_processed['hour'] / 24)
        df_processed['day_of_week_num'] = self._day_of_week_to_number(df_processed['day_of_week'])
        
        # Feature: is_weekend
        df_processed['is_weekend'] = df_processed['day_of_week_num'].isin([5, 6]).astype(int)
        
        # Feature: severity_level mapping numerico
        severity_map = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        df_processed['severity_level'] = df_processed['severity'].map(severity_map).fillna(1)
        
        # Feature: status_failure
        df_processed['status_failure'] = (df_processed['status'].str.lower() == 'failure').astype(int)
        
        # Feature: event_complexidad (caracteristicas tecnicas combinadas)
        df_processed['has_method'] = df_processed['method'].notna().astype(int)
        df_processed['has_trace'] = df_processed['trace_id'].notna().astype(int)
        
        # Features para modelos de latencia/anomalias
        df_processed['log_duration'] = np.log1p(df_processed['duration_ms'])
        df_processed['status_code_is_error'] = (df_processed['status_code'] >= 400).astype(int)
        
        # Caracteristica de risk score composite
        df_processed['risk_score'] = (
            df_processed['severity_level'] * 0.4 +
            df_processed['status_failure'] * 0.3 +
            df_processed['log_duration'] / df_processed['log_duration'].max() * 0.2 +
            df_processed['is_weekend'] * 0.1
        )
        
        # Limpiar NaNs
        numeric_cols = ['hour_sin', 'hour_cos', 'day_of_week_num', 'is_weekend', 
                       'severity_level', 'status_failure', 'has_method', 'has_trace',
                       'log_duration', 'status_code_is_error', 'risk_score']
        
        for col in numeric_cols:
            if col in df_processed.columns:
                df_processed[col] = df_processed[col].fillna(df_processed[col].median())
        
        return df_processed, numeric_cols
    
    def _day_of_week_to_number(self, day_of_week: pd.Series) -> pd.Series:
        """Convertir string de dia a numero."""
        mapping = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6,
            'lunes': 0, 'martes': 1, 'jueves': 3, 'viernes': 4, 'sabado': 5, 'domingo': 6
        }
        return day_of_week.str.lower().map(mapping).fillna(0).astype(int)
    
    def get_feature_columns(self):
        """Obtener nombres de columnas de features."""
        return self.numeric_features + [
            'hour_sin', 'hour_cos', 'day_of_week_num', 'is_weekend',
            'severity_level', 'status_failure', 'has_method', 'has_trace',
            'log_duration', 'status_code_is_error', 'risk_score'
        ]

class FeaturePipeline:
    """Pipeline completo de features para el pipeline AIOps."""
    
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.is_fitted = False
    
    def fit(self, df):
        """Entrenar pipeline de features."""
        self.feature_engineer.fit_transform(df)
        self.is_fitted = True
        return self
    
    def transform(self, df):
        """Transformar DataFrame usando features entrenadas."""
        if not self.is_fitted:
            raise ValueError("FeaturePipeline no esta entrenado. Llamar fit primero.")
        
        df_processed, numeric_cols = self.feature_engineer.fit_transform(df)
        return df_processed, numeric_cols
    
    def get_feature_names(self):
        """Obtener nombres de columnas de features."""
        return self.feature_engineer.get_feature_columns()

# Modelo de feature dataset para esquema SQL
from pydantic import BaseModel

class EventFeatures(BaseModel):
    """Modelo Pydantic para features en almacenamiento."""
    received_at: str
    environment: str
    project: str
    hostname: str
    instance_id: str
    event_type: str
    category: str
    severity: str
    status: str
    status_code: float
    duration_ms: float
    hour: int
    day_of_week: str
    method: str
    path: str
    line: float
    logger_name: str
    level: str
    risk_score: float
    is_weekend: int
    severity_level: int
    status_failure: int
    log_duration: float
    status_code_is_error: int

# Exportar entidades clave
__all__ = ['FeatureEngineer', 'FeaturePipeline', 'EventFeatures']