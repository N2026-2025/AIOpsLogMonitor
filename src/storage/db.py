from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Optional
import os


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/aioplogmonitor")

_engine = None


def get_engine():
    """Crear engine SQLAlchemy (singleton para reutilizar pool de conexiones)."""
    global _engine
    if _engine is None:
        engine_kwargs = {"pool_pre_ping": True}
        if DATABASE_URL.startswith("sqlite"):
            engine_kwargs["poolclass"] = StaticPool
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(DATABASE_URL, **engine_kwargs)
    return _engine

def get_session_factory():
    """Crear factory de sesiones."""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal

def init_database()::
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
