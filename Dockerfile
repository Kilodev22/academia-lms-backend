# Usa una imagen oficial de Python como base
FROM python:3.9-slim

# Instala las dependencias del sistema operativo que WeasyPrint necesita
RUN apt-get update && apt-get install -y \
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

# Expone el puerto que usará Gunicorn
EXPOSE 8000

# Comando para iniciar la aplicación en producción
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "academy:create_app()"]