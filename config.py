import os
from dotenv import load_dotenv
from datetime import timedelta 
# Carga las variables de un archivo .env si existe (para desarrollo local)
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv()

class Config:
    # Claves secretas para la seguridad.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    # --- NUEVAS CLAVES PARA GOOGLE OAUTH ---
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    FRONTEND_URL = os.environ.get('FRONTEND_URL')

    # --- Lógica Definitiva para la Conexión a la Base de Datos ---
    
    # 1. Obtenemos la URL de la base de datos.
    db_url = os.environ.get('DATABASE_URL')
    
    # 2. Preparamos un diccionario para las opciones de conexión.
    engine_options = {}

    if db_url:
        # 3. Reemplazamos el esquema para usar el conector correcto para Vercel.
        if db_url.startswith("mysql://"):
            db_url = db_url.replace("mysql://", "mysql+mysqlconnector://", 1)
        
        # 4. Si la URL requiere SSL, quitamos esa parte de la URL...
        if '?ssl_mode=REQUIRED' in db_url:
            db_url = db_url.split('?')[0]
            # 5. ...y en su lugar, le pasamos el argumento correcto al conector.
            #    Para mysql-connector-python, 'ssl_disabled': False es el equivalente
            #    a requerir una conexión SSL.
            engine_options['connect_args'] = {'ssl_disabled': False}

    # 6. Asignamos la URL limpia y las opciones de conexión por separado.
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_ENGINE_OPTIONS = engine_options
    
    # 7. Desactivamos una función de SQLAlchemy que no se usa y consume recursos.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
