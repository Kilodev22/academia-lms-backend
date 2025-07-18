# academy/models.py

from .extensions import db 
from datetime import datetime

# ==============================================================================
# TABLA DE ASOCIACIÓN (Muchos a Muchos entre User y Course)
# ==============================================================================
enrollment_table = db.Table('enrollment',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True),
    db.Column('enrolled_at', db.DateTime, default=datetime.utcnow)
)

# ==============================================================================
# MODELO USER (ACTUALIZADO)
# ==============================================================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    last_jti = db.Column(db.String(36), nullable=True) # JTI is typically a UUID (36 chars)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_jti = db.Column(db.String(36), nullable=True) # El JTI es típicamente un UUID (36 caracteres)

    created_courses = db.relationship('Course', backref='instructor', lazy=True)

    # --- ¡CORRECCIÓN DEFINITIVA AQUÍ! ---
    # Cambiamos lazy='dynamic' por lazy=True.
    # Esto soluciona el error de "eager loading" en Flask-Admin de raíz.
    enrolled_courses = db.relationship('Course', secondary=enrollment_table, backref='enrolled_users', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

# ==============================================================================
# MODELO COURSE (NUEVO)
# ==============================================================================
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # --- LÍNEA AÑADIDA ---
    # Este campo guardará el enlace a la imagen del curso.
    image_url = db.Column(db.String(255), nullable=True)

    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lessons = db.relationship('Lesson', backref='course', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
       return f'<Course {self.title}>'

# ==============================================================================
# MODELO LESSON (NUEVO)
# ==============================================================================
class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Float, nullable=False)

    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    def __repr__(self):
        return f'<Lesson {self.title}>'
