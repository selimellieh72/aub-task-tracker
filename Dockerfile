# Task Tracker API — production-style image (API only; the frontend is a static
# folder you open from disk or serve separately).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# Install dependencies first so this layer is cached between code changes.
COPY app/requirements.txt ./app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

# Only the application package is copied (see .dockerignore for what is excluded).
COPY app/ ./app/

# Run as an unprivileged user.
RUN useradd --system --uid 1001 --no-create-home appuser \
    && chown -R appuser:appuser /srv
USER appuser

EXPOSE 8000

# Container-level health check against the existing /health endpoint
# (python is used because the slim image has no curl).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
