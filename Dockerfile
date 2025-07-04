# Usa una imagen oficial de Python como base
FROM python:3.9-slim

# Instala las dependencias del sistema que WeasyPrint necesita
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /var/task

# Copia e instala las dependencias de Python
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de tu aplicación
COPY . .

# Asegura que el script de inicio sea ejecutable
RUN chmod +x /var/task/run.sh

# Expone el puerto que usará Gunicorn
EXPOSE 8080

# Comando para iniciar la aplicación a través del script
CMD ["/var/task/run.sh"]