# AIOps Log Monitor / Legacy-Bridge

Implementa la metodología STAR: observabilidad de sistemas heredados + triaje inteligente (AIOps) con ML explicable.

## Problemática

- Según reportes tecnológicos de Accenture y Thoughtworks 2026, las empresas destinan hasta el 70% de su presupuesto IT a mantener sistemas heredados (legacy) y aplicaciones en la nube.
- Con el ritmo acelerado de desarrollo actual, los sistemas generan miles de registros de eventos (logs) por minuto.
- Los equipos de soporte técnico, QA y desarrollo pierden horas revisando archivos manualmente para descubrir por qué cayó un servicio.
- Las degradaciones silenciosas (picos de latencia) disparan costos de servidores sin ser detectadas a tiempo.

## Solución

- **Ingesta**: Pipeline en Python (pandas) que limpia los datos crudos del AIOps Log Monitoring Dataset y los almacena en una base de datos SQL estructurada por entorno, instancia y servicio.
- **Modelado Explicable**: Algoritmos de ML interpretables (Árbol de Decisión / Random Forest para predecir fallos y gravedad según latencia, códigos HTTP y ruta; e Isolation Forest para aislar picos anómalos).
- **Interfaz**: API REST en FastAPI que filtra incidentes por prioridad, muestra variables que impulsan cada falla (location, horario, latencia), con explicaciones basadas en SHAP y árbols.
- **Impacto**: Reducción MTTR, prevención de fallos, detección temprana de degradaciones, escalabilidad empresarial.

## Uso rápido

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Arrancar PostgreSQL (Docker Compose incluido) y crear el esquema:
   ```bash
   python -m src.storage.init init
   ```
3. Ingestar datos de ejemplo (descomentar el comando para cargar el sample de Kaggle):
   ```bash
   python -m src.ingestion.parse data/sample.csv
   ```
4. Entrenar modelos:
   ```bash
   python -m src.ml.train
   ```
5. Arrancar API:
   ```bash
   python -m src.api.main
   ```

## Documentación

- **README STAR** (este bloque) – para reclutadores.
- **ARCHITECTURE** – diseño técnico.
- **SETUP** – inicio paso a paso.

## Licencia
MIT
