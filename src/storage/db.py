from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/aioplogmonitor")

def get_engine():
    """Crear engine SQLAlchemy."""
    return create_engine(DATABASE_URL, pool_pre_ping=True)

def get_session_factory():
    """Crear factory de sesiones."""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal

def init_database():
    """Inicializar base de datos y crear tablas."""
    from src.storage import models
    
    engine = get_engine()
    models.Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

def get_session() -> Session:
    """Obtener sesión de base de datos."""
    SessionLocal = get_session_factory()
    return SessionLocal()

def close_session(session: Session):
    """Cerrar sesión de base de datos."""
    session.close()

def execute_raw(session: Session, statement: str, params: Optional[dict] = None):
    """Ejecutar statement SQL."""
    result = session.execute(text(statement), params or {})
    session.commit()
    return result
