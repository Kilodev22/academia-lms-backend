# academy/__init__.py

from flask import Flask
from config import Config
from .extensions import db, migrate, bcrypt, jwt
from . import models
from flask_cors import CORS

# 1. Importa la instancia de admin que creamos
from .admin import admin_instance

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)

    # 2. Inicializa el panel de administración con la aplicación
    admin_instance.init_app(app)

    # Inicializa el resto de las extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Importa y registra el "plano" de rutas
    from .routes import main_routes
    app.register_blueprint(main_routes)

    return app
