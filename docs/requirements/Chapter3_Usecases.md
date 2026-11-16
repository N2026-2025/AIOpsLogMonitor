# Capítulo 3: Casos de Uso (Use Cases)

## UC-001: Triaje de incidente crítico
**Actor**: Operador de soporte / SRE  
**Descripción**: El operador recibe una alerta de latencia alta y consulta el sistema para determinar si es un fallo real, su gravedad y por qué ocurrió.
1. Operator visita `GET /health` → API respondiendo ✅
2. Operator envía features del evento via `POST /api/v1/predict`:
   - features: `{event_type: "LOG", severity: "HIGH", status: "FAILURE", duration_ms: 5.0, status_code: 500, hour: 14}`
3. API retorna predicción: failure=true, confidence=0.97, severity="HIGH"
4. Operator consulta explicación via `POST /api/v1/explain`:
   - recibe SHAP values y decision path
   - ejemplo top contributing: `severity_level: 0.45 favoring failure`, `status_failure: 0.32 favoring failure`
5. Operator identifica la raíz causa y toma acción correctiva.

**Resultado esperado**: MTTR reducido, decisión en < 2 minutos.

---

## UC-002: Monitoreo continuo de servicios legacy
**Actor**: Equipo de operaciones  
**Descripción**: El equipo monitorea múltiples servicios legacy y recibe alertas cuando se superan umbrales.
1. Equipo configura alertas Prometheus:
   - `HighErrorRate`: >10% errores 5xx en 5 min → crítico
   - `HighLatency`: p95 latencia > 2s → warning
   - `HighPredictionVolume`: >100 predicciones/10 min → warning
2. El dashboard React (`http://localhost:5173`) muestra KPIs en tiempo real.
3. Cuando se dispara `HighErrorRate`, el operador consulta:
   - `GET /api/v1/incidents?min_severity=HIGH` → lista incidentes prioritizados.
   - `GET /api/v1/events?environment=prod&status=FAILURE&limit=100` → eventos problemáticos.
4. El operador filtra por severidad y ambiente, identifica patrones.

**Resultado esperado**: Detección temprana de degradaciones, reducción de costos de servidores.

---

## UC-003: Ingestión y análisis de nuevos logs
**Actor**: Ingeniero de datos / Dev  
**Descripción**: El ingeniero necesita ingestar un nuevo archivo de logs y tenerlos disponibles para consulta y modelado.
1. Ingeniero coloca el CSV nuevo en `data/nuevo_logs.csv`.
2. Ejecuta `python -m src.ingestion.parse data/nuevo_logs.csv`.
3. System procesa el archivo, persiste eventos en PostgreSQL.
4. Ejecuta `python -m src.ml.train` para re-entrenar modelos con los nuevos datos.
5. Los nuevos modelos se guardan en `src/artifacts/aioplogmonitor_models_v0.1.0.pkl`.
6. API queda lista para predicciones con los datos actualizados.

**Resultado esperado**: Pipeline reproducible, sin intervención manual.

---

## UC-004: Verificación de modelo en CI/CD
**Actor**: Integración continua  
**Descripción**: El pipeline CI debe verificar que los modelos entrenados cumplen métricas mínimas.
1. Pipeline se ejecuta en `push` a `main`.
2. Job `test`: `pytest tests/ -v` → 10/10 tests pass ✅
3. Job `security`: gitleaks, semgrep, trivy sin hallazgos críticos.
4. Job `build`: `python -m src.ml.train` → modelo entrenado.
5. Job `deploy`: si todos los anteriores pasan, despliega a Render.
6. Si falla cualquier job, deploy se bloquea y se notifica.

**Resultado esperado**: Deploy solo en main cuando calidad verificada.

---

## UC-005: Baseline de rendimiento para revisores
**Actor**: Revisor / Auditor  
**Descripción**: El revisor necesita números consistentes para validar que el proyecto cumple requisitos.
1. Ejecutar `make test` → 10 passed.
2. Ejecutar `make seed` → 200 eventos deterministas, 25% fallo.
3. Ejecutar `python -m src.ml.train` → accuracy fallo 1.0.
4. Ejecutar `curl http://localhost:8000/health` → {"status":"ok"}.
5. Ejecutar `curl http://localhost:8000/metrics` → contiene `aioplog_api_requests_total`.
6. Ejecutar `curl -X POST http://localhost:8000/api/v1/predict` → predicción con confidence.

**Resultado esperado**: Números verificables, sin aleatoriedad oculta.

---

### Tabla resumen de casos de uso

| # | Caso de Uso | Actor | Objetivo Clave | Endpoints Clave |
|---|-------------|-------|----------------|-----------------|
| UC-001 | Triaje crítico | Operador SRE | Decisión en <2 min | /predict, /explain, /health |
| UC-002 | Monitoreo continuo | Equipo Ops | Alertas proactivas | /events, /incidents, /metrics |
| UC-003 | Ingestión nuevos logs | Ingeniero datos | Pipeline reproducible | /parse, /train, /persist |
| UC-004 | Baseline CI/CD | CI pipeline | Calidad antes deploy | /test, /security, /build |
| UC-005 | Baseline revisor | Auditor | Números consistentes | /health, /metrics, /predict |