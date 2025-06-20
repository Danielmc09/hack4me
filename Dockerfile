########################################
# 1) Builder: instala deps de Python 
########################################
FROM python:3.9-slim AS builder

WORKDIR /app
COPY requirements.txt .

# --prefix instala librerías en /install/lib y scripts en /install/bin
RUN pip install --no-cache-dir \
    --compile \
    --prefix=/install \
    -r requirements.txt

########################################
# 2) Runtime: Python 3.9-slim con nmap + wkhtmltopdf
########################################
FROM python:3.9-slim AS runtime

WORKDIR /app

# Instalación mínima de binarios nativos
RUN apt-get update \
 && apt-get install -y --no-install-recommends nmap wkhtmltopdf \
 && rm -rf /var/lib/apt/lists/*

# Copiamos librerías y scripts (uvicorn, etc.) al sitio de instalación de runtime
COPY --from=builder /install /usr/local

# Tu código
COPY . .

EXPOSE 8000

# uvicorn estará disponible en /usr/local/bin/uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
