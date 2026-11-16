from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Event(Base):
    """Modelo ORM para eventos de log."""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, index=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    environment = Column(String, nullable=False, index=True)
    project = Column(String, nullable=False)
    hostname = Column(String, nullable=False)
    instance_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    category = Column(String)
    severity = Column(String)
    status = Column(String)
    status_code = Column(Float)
    duration_ms = Column(Float)
    hour = Column(Integer)
    day_of_week = Column(String)
    method = Column(String)
    path = Column(String)
    line = Column(Float)
    logger_name = Column(String)
    level = Column(String)
    risk_score = Column(Float)
    is_weekend = Column(Boolean)
    severity_level = Column(Integer)
    status_failure = Column(Boolean)
    log_duration = Column(Float)
    status_code_is_error = Column(Boolean)
    schema_version = Column(String)
    sdk_version = Column(String)
    app_version = Column(String)
    trace_id = Column(String)
    message = Column(Text)
    process_id = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    predictions = relationship('Prediction', back_populates='event', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convertir a diccionario."""
        return {
            'id': self.id,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'environment': self.environment,
            'project': self.project,
            'hostname': self.hostname,
            'instance_id': self.instance_id,
            'event_type': self.event_type,
            'category': self.category,
            'severity': self.severity,
            'status': self.status,
            'status_code': self.status_code,
            'duration_ms': self.duration_ms,
            'hour': self.hour,
            'day_of_week': self.day_of_week,
            'method': self.method,
            'path': self.path,
            'line': self.line,
            'logger_name': self.logger_name,
            'level': self.level,
            'risk_score': self.risk_score,
            'is_weekend': self.is_weekend,
            'severity_level': self.severity_level,
            'status_failure': self.status_failure,
            'log_duration': self.log_duration,
            'status_code_is_error': self.status_code_is_error,
            'schema_version': self.schema_version,
            'sdk_version': self.sdk_version,
            'app_version': self.app_version,
            'trace_id': self.trace_id,
            'message': self.message,
            'process_id': self.process_id,
        }

# Tabla de predicción (para auditoría/explicabilidad)
class Prediction(Base):
    """Modelo ORM para predicciones con explicación."""
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    failure_probability = Column(Float)
    severity_prediction = Column(String)
    anomaly_score = Column(Float)
    model_version = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    event = relationship('Event', back_populates='predictions')
    
    def to_dict(self):
        """Convertir a diccionario."""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'failure_probability': self.failure_probability,
            'severity_prediction': self.severity_prediction,
            'anomaly_score': self.anomaly_score,
            'model_version': self.model_version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
