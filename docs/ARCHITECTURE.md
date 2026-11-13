# ARCHITECTURE — AIOps Log Monitor (HLD)

## 1. Overview

**AIOps Log Monitor / Legacy-Bridge** es un sistema de observabilidad y triaje inteligente (AIOps) para aplicaciones legacy. Su objetivo es transformar miles de registros de logs crudos en incidentes priorizados, detectar degradaciones silenciosas y explicar *qué módulo* del código está provocando cada fallo, con soporte de Machine Learning interpretable.

## 2. Problema que resuelve

- Los equipos de soporte, QA y desarrollo pierden horas revisando logs manualmente.
- Las degradaciones silenciosas (picos de latencia) aumentan costos de infraestructura sin ser detectadas a tiempo.
- Los sistemas legacy generan volúmenes altos de eventos que no son triados ni alertados de forma automática.

## 3. Solución en alto nivel

```
[Legacy / Fuentes de logs] -> [Ingestion Service] -> [PostgreSQL]
                                                      |
[Dataset de entrenamiento] -> [ML Pipeline] -> [Modelos interpretables]
                                                      |
[API REST (FastAPI)] <-> [ML Pipeline] <-> [Explicabilidad (SHAP)]
                                                      |
[Usuario / Soporte] -> [Consulta de incidentes priorizados]
```

## 4. Stack tecnológico confirmado

| Capa | Tecnología | Justificación |
|------|------------|---------------|
| Lenguaje | Python >= 3.9 | Ecosistema ML robusto, fácil de mantener |
| API REST | FastAPI + Uvicorn + Pydantic v2 | Validación automática, documentación OpenAPI integrada, alto rendimiento |
| ETL / Ingesta | Pandas + SQLAlchemy 2.0 | Procesamiento de tablas, migración fácil a SQL |
| Base de datos | PostgreSQL (producción) / SQLite (tests) | Trazabilidad por entorno/instancia/servicio, consultas flexibles |
| ML | scikit-learn + SHAP | Árboles de decisión e Isolation Forest interpretables, explicabilidad auditable |
| Tests | pytest + TestClient | Cobertura de integración y unidades |

## 5. Arquitectura por contenedores

```mermaid
C4Container
  title Contenedores del Sistema AIOps Log Monitor

  Container(user, "Usuario / Soporte", "Accede a incidentes y explicaciones", "Web / CLI / API")
  Container(ing, "Ingestion Service", "Limpia y carga logs crudos en SQL", "Python / Pandas")
  Container(storage, "Storage Layer", "Persistence relacional: entornos, instancias, servicios, eventos", "SQLAlchemy + PostgreSQL")
  Container(ml, "ML Pipeline", "Predicción de fallos, anomalías, explicabilidad", "scikit-learn + SHAP")
  Container(api, "API REST", "Endpoints de salud, predicción y explicación", "FastAPI + Uvicorn")

  Rel(user, api, "Consulta / explica incidentes", "HTTPS / JSON")
  Rel(ing, storage, "Escribe eventos estructurados", "SQL")
  Rel(ml, storage, "Lee datos para entrenamiento e inferencia", "SQL")
  Rel(api, ml, "Solicita predicciones y explicaciones", "Invocación en-proceso")
  Rel(api, storage, "Consulta incidentes filtrados", "SQL")
