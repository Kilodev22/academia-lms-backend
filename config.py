# config.py

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # --- AÑADE ESTAS LÍNEAS PARA DEPURAR ---
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("mysql://"):
     db_url = db_url.replace("mysql://", "mysql+mysqlconnector://", 1)

    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

