# Dockerfile — AIOps Log Monitor
# Build: docker build -t aiops-log-monitor .
# Run:   docker run -p 8000:8000 aiops-log-monitor
FROM python:3.11-slim

# Metadatos
LABEL project="aiops-log-monitor"
LABEL version="0.1.0"

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias primero (cache de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorio de artefactos (el modelo se genera con `python -m src.ml.train`)
RUN mkdir -p /app/src/artifacts

# Exponer puerto de la API FastAPI
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Comando: levantar la API FastAPI
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]