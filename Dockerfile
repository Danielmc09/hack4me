FROM python:3.12.11-bullseye AS build

WORKDIR /app

ENV PYTHON_PACKAGES_DIR=/install/python_packages

RUN mkdir -p ${PYTHON_PACKAGES_DIR}

COPY requirements.txt .

RUN pip install --no-cache-dir --compile -r requirements.txt --target=${PYTHON_PACKAGES_DIR}


# Instalar solo lo necesario
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#     python3 python3-pip python3-venv nmap wkhtmltopdf curl && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# # Carpeta de trabajo
# WORKDIR /app

# # Crear un entorno virtual
# RUN python3 -m venv /app/venv

# # Activar el entorno virtual y actualizar pip
# ENV PATH="/app/venv/bin:$PATH"

# # Copiar dependencias y app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY app/ ./

# EXPOSE 8000

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y nmap wkhtmltopdf

ENV PYTHON_PACKAGES_DIR=/app/python_packages
ENV PYTHONPATH=${PYTHON_PACKAGES_DIR}:${PYTHONPATH}

COPY --from=build /install/python_packages ${PYTHON_PACKAGES_DIR}

COPY ./app .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]