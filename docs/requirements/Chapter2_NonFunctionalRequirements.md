# Capítulo 2: Requisitos No-Funcionales (Chapter 24.3 - Req-NFR)

## Calidad, rendimiento, seguridad y operabilidad

### NFR-001: Rendimiento (Performance)
- **RF-010**: Latencia de predicción en tiempo real < 100ms.
- **Ingesta**: 1746 eventos procesados en < 5s (pandas vectorizado).
- **Entrenamiento**: modelos entrenados en < 15s (n_jobs=-1, 1746 filas).
- **Escalabilidad**: Horizontal scaling stateless detrás de load balancer.

### NFR-002: Escalabilidad
- **Ingesta chunked**: 10k filas por lote (configurable).
- **Modelos**: `n_jobs=-1` usa todos los cores.
- **PostgreSQL**: índices en timestamp, environment, severity, status.
- **Arquitectura stateless**: API puede replicarse horizontalmente.

### NFR-003: Seguridad
- **Validación Pydantic**: todos los endpoints validan payloads con schemas estrictos.
- **SQL parameterizado**: SQLAlchemy ORM previene SQL injection.
- **No ejecución dinámica**: no `eval()`, no `exec()` en código de producción.
- **Errores genéricos**: en producción se retorna mensaje genérico, no stack trace.
- **Secretos**: nunca commitear API keys, DB URLs (gitleaks config incluido).

### NFR-004: Confiabilidad y disponibilidad
- **Healthcheck**: `GET /health` retorna 200 con `{"status": "ok"}`.
- **Graceful degradation**: DB init no bloquea arranque si PostgreSQL no disponible.
- **Retry**: reintentos en deploy de Render.
- **Uptime goal**: 99% mensual (free tier puede dormir, trade-off documentado).

### NFR-005: Observabilidad
- **Métricas**: Prometheus `aioplog_api_requests_total`, `aioplog_api_request_duration_seconds`.
- **Alertas**: `HighErrorRate` (>10% 5xx), `HighLatency` (p95 >2s), `HighPredictionVolume`.
- **Tracing**: OpenTelemetry spans exportados a Tempo (via OTLP).
- **Logs**: structured logging con `trace_id` correlado.

### NFR-006: Mantenibilidad
- **Docs**: `docs/ARCHITECTURE.md`, `docs/LLD.md`, `docs/API_CONTRACT.md`, `docs/SETUP.md`, `docs/requirements/`.
- **Tests**: 10 tests, 100% cobertura de features críticas.
- **Lint**: flake8 con `--max-line-length=120`.
- **CI/CD**: pipeline reproducible en `.github/workflows/ci.yml`.

### NFR-007: Portabilidad
- **Python**: >= 3.11 (compatible 3.14).
- **OS**: Windows 11, Linux, macOS (Docker Compose).
- **Docker**: imagen `python:3.11-slim` (Dockerfile).
- **Render**: deploy blueprint (render.yaml).

### NFR-008: Usabilidad
- **API REST**: OpenAPI auto-generado por FastAPI (`/docs`).
- **React dashboard**: consume la API, muestra KPIs, predicciones y explicaciones.
- **CLI**: comandos bash documentados (`python -m src.*`).

### NFR-009: Trazabilidad
- **Trazabilidad de datos**: `ingested_at`, `source_file`, `trace_id` en cada evento.
- **Versionado de modelos**: `model_version = "0.1.0"` en artefactos.
- **Explicabilidad**: cada predicción tiene SHAP values y decision path.

### NFR-010: Costo
- **Free tier**: Render PostgreSQL gratis 30 días.
- **Cold start**: servicio web duerme cuando inactivo (~tens of seconds).
- **Budget**: sin costos de infraestructura fijos.

---

### Tabla de cobertura de requisitos no-funcionales

| # | Requisito | Categoría | Evidencia | Estado |
|---|-----------|-----------|-----------|--------|
| NFR-001 | Rendimiento < 100ms | Performance | benchmark predict | implementation |
| NFR-002 | Escalabilidad chunked | Scalability | IngestService config | ✅ |
| NFR-003 | Validación Pydantic | Security | schemas + gitleaks/semgrep | ✅ |
| NFR-004 | Healthcheck DB graceful | Reliability | init_database try/except | ✅ |
| NFR-005 | Métricas Prometheus | Observability | `/metrics` endpoint | ✅ |
| NFR-006 | 10 tests passing | Maintainability | pytest | ✅ |
| NFR-007 | Python 3.11+ / Docker | Portability | Dockerfile + Render | ✅ |
| NFR-008 | React dashboard | Usability | `frontend/` SPA | ✅ |
| NFR-009 | trace_id correlado | Traceability | Event model + OTEL | ✅ |
| NFR-010 | Free tier aware | Cost | render.yaml free plan | ✅ |