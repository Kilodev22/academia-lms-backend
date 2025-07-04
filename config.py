import os
from dotenv import load_dotenv

# Carga las variables de un archivo .env si existe (para desarrollo local)
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Claves secretas para la seguridad de la sesión y los tokens JWT.
    # Es crucial que estas estén definidas en las variables de entorno de Vercel.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    # --- Lógica Correcta para la Conexión a la Base de Datos ---
    
    # 1. Obtenemos la URL de la base de datos.
    db_url = os.environ.get('DATABASE_URL')
    
    # 2. Si es una URL de MySQL, la modificamos para que sea compatible con Vercel.
    if db_url and db_url.startswith("mysql://"):
        db_url = db_url.replace("mysql://", "mysql+mysqlconnector://", 1)
    
    # 3. Asignamos la URL (ya corregida) a la configuración de SQLAlchemy.
    SQLALCHEMY_DATABASE_URI = db_url
    
    # 4. Desactivamos una función de SQLAlchemy que no se usa y consume recursos.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
