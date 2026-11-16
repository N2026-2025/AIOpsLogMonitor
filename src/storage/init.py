from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from src.storage.db import get_engine, get_session_factory, init_database, close_session, execute_raw
from src.storage import models


class StorageService:
    """Servicio principal para almacenamiento en PostgreSQL."""
    
    def __init__(self, database_url: Optional[str] = None):
        if database_url:
            import os
            os.environ['DATABASE_URL'] = database_url
    
    def init(self):
        """Inicializar esquema de base de datos."""
        init_database()
    
    def store_events(self, session: Session, events_df):
        """Almacenar eventos en base de datos."""
        stored_count = 0
        for _, row in events_df.iterrows():
            event = models.Event(
                received_at=datetime.now(),
                environment=str(row.get('environment', 'unknown')),
                project=str(row.get('project', 'unknown')),
                hostname=str(row.get('hostname', 'unknown')),
                instance_id=str(row.get('instance_id', 'unknown')),
                event_type=str(row.get('event_type', 'UNKNOWN')),
                category=str(row.get('category', '')),
                severity=str(row.get('severity', '')),
                status=str(row.get('status', 'UNKNOWN')),
                status_code=float(row.get('status_code', 0)) if pd.notna(row.get('status_code', 0)) else 0.0,
                duration_ms=float(row.get('duration_ms', 0)) if pd.notna(row.get('duration_ms', 0)) else 0.0,
                hour=int(row.get('hour', 0)) if pd.notna(row.get('hour', 0)) else 0,
                day_of_week=str(row.get('day_of_week', '')),
                method=str(row.get('method', '')),
                path=str(row.get('path', '')),
                line=float(row.get('line', 0)) if pd.notna(row.get('line', 0)) else 0.0,
                logger_name=str(row.get('logger_name', '')),
                level=str(row.get('level', '')),
                risk_score=float(row.get('risk_score', 0)) if pd.notna(row.get('risk_score', 0)) else 0.0,
                is_weekend=bool(row.get('is_weekend', 0)) if pd.notna(row.get('is_weekend', 0)) else False,
                severity_level=int(row.get('severity_level', 0)) if pd.notna(row.get('severity_level', 0)) else 0,
                status_failure=bool(row.get('status_failure', 0)) if pd.notna(row.get('status_failure', 0)) else False,
                log_duration=float(row.get('log_duration', 0)) if pd.notna(row.get('log_duration', 0)) else 0.0,
                status_code_is_error=bool(row.get('status_code_is_error', 0)) if pd.notna(row.get('status_code_is_error', 0)) else False,
                schema_version=str(row.get('schema_version', '')),
                sdk_version=str(row.get('sdk_version', '')),
                app_version=str(row.get('app_version', '')),
                trace_id=str(row.get('trace_id', '')),
                message=str(row.get('message', '')) if pd.notna(row.get('message', '')) else None,
                process_id=int(row.get('process_id', 0)) if pd.notna(row.get('process_id', 0)) else 0,
            )
            session.add(event)
            stored_count += 1
        
        session.commit()
        return stored_count

    def get_events(self, session: Session, environment=None, severity=None, status=None, limit: int = 100):
        """Obtener eventos filtrados."""
        query = session.query(models.Event)
        
        if environment:
            query = query.filter(models.Event.environment == environment)
        if severity:
            query = query.filter(models.Event.severity == severity)
        if status:
            query = query.filter(models.Event.status == status)
        
        return query.limit(limit).all()

    def get_incidents(self, session: Session, min_severity: str = 'HIGH', limit: int = 100):
        """Obtener incidentes priorizados."""
        severity_order = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        min_level = severity_order.get(min_severity.upper(), 0)
        
        query = session.query(models.Event).filter(
            models.Event.status_failure is True,
        )
        
        if min_level >= 2:
            query = query.filter(models.Event.severity_level >= 2)
        elif min_level >= 1:
            query = query.filter(models.Event.severity_level >= 1)
        
        return query.order_by(models.Event.risk_score.desc()).limit(limit).all()


import pandas as pd
__all__ = ['StorageService']


def main():
    """CLI: inicializar esquema de base de datos."""
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else 'init'
    if action == 'init':
        init_database()
        print("Database schema initialized successfully.")
    else:
        print(f"Unknown action: {action}. Use 'init'.")


if __name__ == "__main__":
    main()
