# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Actualiza los paquetes del sistema e instala las dependencias de WeasyPrint
# Esto es clave para solucionar el error de Pango
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-cffi \
    libcairo2 \
    pango1.0-tools \
    libpangocairo-1.0-0 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requerimientos e instala las dependencias de Python
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación
COPY . .

# Expone el puerto que usa tu aplicación (ajusta si es necesario)
EXPOSE 8000

# Comando para iniciar la aplicación con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "manage:app"]