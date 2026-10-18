# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Sin .pyc, logs sin búfer y pip sin caché: imagen más pequeña y logs inmediatos
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Las dependencias se instalan antes de copiar el código para aprovechar la caché de capas
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY manage.py ./
COPY config ./config
COPY representacion ./representacion

# Usuario sin privilegios: el proceso no corre como root dentro del contenedor
RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/salud/', timeout=2).status == 200 else 1)"

# gunicorn (servidor WSGI de producción) en lugar de runserver.
# 2 workers x 2 hilos caben con holgura en 256 MB y 1 CPU.
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", \
     "--max-requests", "1000", "--max-requests-jitter", "100", \
     "--access-logfile", "-"]
