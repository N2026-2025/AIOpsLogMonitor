import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ValidationError
import sys

class IngestionConfig(BaseModel):
    """Configuration for ingestion pipeline."""
    chunk_size: int = Field(default=10000, ge=1, description="Tamaño del chunk para lectura CSV")
    batch_size: int = Field(default=1000, ge=1, description="Tamaño del batch para inserción")
    encoding: str = Field(default="utf-8", description="Encoding del archivo CSV")

class EventParser:
    """Parser para schema del AIOps Log Monitoring Dataset."""
    
    @staticmethod
    def parse_csv(file_path: str, config: Optional[IngestionConfig] = None) -> pd.DataFrame:
        """Parse CSV file to DataFrame with cleaning and validation."""
        if config is None:
            config = IngestionConfig()
        
        try:
            # Leer CSV con dtype para mantener tipos correctos
            df = pd.read_csv(
                file_path,
                encoding=config.encoding,
                dtype={
                    'received_at': str,
                    'environment': str,
                    'project': str,
                    'event_count': int,
                    'schema_version': str,
                    'sdk_version': str,
                    'event_type': str,
                    'category': str,
                    'severity': str,
                    'status': str,
                    'timestamp': str,
                    'hostname': str,
                    'os': str,
                    'os_version': str,
                    'python_version': str,
                    'region': str,
                    'app_version': str,
                    'instance_id': str,
                    'process_id': int,
                    'trace_id': str,
                    'message': str,
                    'file': str,
                    'line': float,
                    'logger_name': str,
                    'level': str,
                    'method': str,
                    'path': str,
                    'status_code': float,
                    'duration_ms': float,
                    'hour': int,
                    'date': str,
                    'day_of_week': str,
                    'month': int,
                    'week': int,
                    'day': int
                }
            )
        except Exception as e:
            raise ValueError(f"Error parsing CSV {file_path}: {e}")
        
        # Limpiar y normalizar
        df = EventParser._clean_dataframe(df)
        
        # Validar required fields
        required_fields = ['event_type', 'severity', 'status', 'hostname', 'instance_id']
        missing_fields = [f for f in required_fields if f not in df.columns]
        if missing_fields:
            raise ValueError(f"Missing required fields after cleaning: {missing_fields}")
        
        # Agregar timestamp de procesamiento
        df['received_at_processing'] = pd.Timestamp.now(tz='UTC')
        
        return df
    
    @staticmethod
    def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize DataFrame."""
        # Limpiar mensaje (remover caracteres ANSI escape)
        if 'message' in df.columns:
            df['message'] = df['message'].fillna('').replace(r'\x1b\[[0-9;]*m', '', regex=True)
        
        # Normalizar valores categóricos
        if 'environment' in df.columns:
            df['environment'] = df['environment'].str.lower().str.strip()
        
        if 'severity' in df.columns:
            # Normalizar severidades
            df['severity_norm'] = df['severity'].str.lower().replace({
                'high': 'HIGH', 'low': 'LOW', 'medium': 'MEDIUM'
            })
        
        # Asegurar tipos numéricos
        for col in ['duration_ms', 'status_code', 'line', 'process_id', 'event_count']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Llenar valores nulos
        for col in ['status_code', 'duration_ms', 'line']:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        # Asegurar que valores críticos estén presentes
        if 'status' in df.columns:
            df['status'] = df['status'].fillna('UNKNOWN')
        
        if 'event_type' in df.columns:
            df['event_type'] = df['event_type'].fillna('UNKNOWN')
        
        return df

class IngestionService:
    """Servicio principal para ingesta de datos."""
    
    def __init__(self, config: Optional[IngestionConfig] = None):
        self.config = config or IngestionConfig()
        self.parser = EventParser()
    
    def ingest_file(self, file_path: str) -> pd.DataFrame:
        """Ingest CSV file and return cleaned DataFrame."""
        print(f"Ingesting file: {file_path}")
        df = self.parser.parse_csv(file_path, self.config)
        print(f"Processed {len(df)} records from {file_path}")
        return df

def main():
    """Punto de entrada principal para CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingestor de datos AIOps")
    parser.add_argument("file_path", help="Ruta al archivo CSV")
    parser.add_argument("--chunk-size", type=int, default=10000, help="Tamaño del chunk para lectura CSV")
    parser.add_argument("--batch-size", type=int, default=1000, help="Tamaño del batch para inserción")
    parser.add_argument("--encoding", default="utf-8", help="Encoding del archivo CSV")
    
    args = parser.parse_args()
    
    config = IngestionConfig(
        chunk_size=args.chunk_size,
        batch_size=args.batch_size,
        encoding=args.encoding
    )
    
    service = IngestionService(config)
    df = service.ingest_file(args.file_path)
    
    # Mostrar primeras filas para debugging
    print("\nMuestras de datos procesados:")
    print(df.head())
    print(f"\nShape: {df.shape}")
    print(f"Columnas: {list(df.columns)}")
    
    # Guardar snapshot para inspección rápida
    output_path = Path("data/ingested_sample.parquet")
    df.to_parquet(output_path, index=False)
    print(f"\nSample guardado en: {output_path}")
    
    return df

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
