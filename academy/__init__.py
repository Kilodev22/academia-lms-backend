# academy/__init__.py

from flask import Flask
from config import Config
from .extensions import db, migrate, bcrypt, jwt,oauth 
from . import models
from flask_cors import CORS

# 1. Importa la instancia de admin que creamos
from .admin import admin_instance

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
      # --- LÍNEAS DE DEPURACIÓN ---
   

    # --- ESTA ES LA SECCIÓN CORREGIDA ---
    # Define las URLs (orígenes) que tienen permiso para conectarse.
    origins = ["centrodeinnovacion.digital",
        "https://www.centrodeinnovacion.digital",  # Tu frontend en producción
        "http://127.0.0.1:5500",                      # Para desarrollo local con VS Code Live Server
        "http://localhost:5500",                     # Alternativa para Live Server
        "http://localhost:8000"                      # Para desarrollo local con servidor de Python
    ]
    # Reemplaza CORS(app) con esta configuración más específica.
    CORS(app, resources={r"/*": {"origins": origins}})
    # --- FIN DE LA CORRECCIÓN ---


    # 2. Inicializa el panel de administración con la aplicación
    admin_instance.init_app(app)

    # Inicializa el resto de las extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    # Importa y registra el "plano" de rutas
    from .routes import main_routes
    app.register_blueprint(main_routes)

    return app
