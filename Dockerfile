# 1) Builder: compila y cachea paquetes en ruedas
FROM python:3.12-slim AS builder
WORKDIR /app

# Variables optimizan pip y bytecode
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala compilador para dependencias nativas en un solo layer
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

# Copia solo requirements antes de la aplicación para cache
COPY requirements.txt .

# Genera ruedas para cachear paquetes
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# 2) Runtime: imagen final ligera con nmap y wkhtmltopdf
FROM python:3.12-slim AS runtime
WORKDIR /app

# Instala nmap y wkhtmltopdf para que python-nmap y pdfkit funcionen
RUN apt-get update \
    && apt-get install -y --no-install-recommends nmap wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Crea un usuario no root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copia paquetes pre-compilados y limpia ruedas
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* \
    && rm -rf /wheels

# Copia código de la aplicación
COPY . .

# Ajusta permisos y usuario
RUN chown -R appuser:appgroup /app
USER appuser

# Exponemos el puerto
EXPOSE 8000

# Un solo proceso: uvicorn
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Metadata y versión
LABEL maintainer="tu@correo.com"
LABEL version="1.0.0"