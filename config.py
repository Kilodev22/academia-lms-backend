# config.py

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # --- AÑADE ESTAS LÍNEAS PARA DEPURAR ---
    db_url = os.environ.get('DATABASE_URL')
    print(f"DEBUG: La DATABASE_URL leída es: {db_url}") 
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

