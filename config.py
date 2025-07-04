# config.py

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Clave para firmar los tokens de la API
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
<<<<<<< HEAD
    # --- AÑADE ESTAS LÍNEAS PARA DEPURAR ---
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("mysql://"):
     db_url = db_url.replace("mysql://", "mysql+mysqlconnector://", 1)
=======
    # NUEVO: Clave para firmar la sesión de Flask (usada por Flask-Admin)
    SECRET_KEY = os.environ.get('SECRET_KEY')
>>>>>>> parent of 78e7163 (Añadir print de depuración para DATABASE_URL)

    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

