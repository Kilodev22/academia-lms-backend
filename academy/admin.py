# academy/admin.py

from flask import redirect, url_for, request, session, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from wtforms.fields import PasswordField, SelectField
from .extensions import db, bcrypt
from .models import User, Course, Lesson
import os

# 1. Creamos una vista de índice personalizada y segura
class SecureAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        # Si el usuario no está logueado como admin, lo redirige al login
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        # Si está logueado, muestra la página principal del admin
        return super(SecureAdminIndexView, self).index()

    @expose('/login', methods=['GET', 'POST'])
    def login(self):
        if request.method == 'POST':
            # Usa variables de entorno para el usuario y contraseña en producción
            ADMIN_USER = os.environ.get('ADMIN_USER', 'admin') # Usuario por defecto: admin
            ADMIN_PASS = os.environ.get('ADMIN_PASS', 'supersecreto') # Contraseña por defecto: supersecreto
            
            if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
                session['admin_logged_in'] = True
                return redirect(url_for('admin.index'))
            else:
                flash('Usuario o contraseña incorrectos.', 'error')
        return self.render('admin/login.html') # Renderiza la plantilla de login

    @expose('/logout')
    def logout(self):
        session.pop('admin_logged_in', None)
        flash('Has cerrado sesión.', 'success')
        return redirect(url_for('admin.login'))

# 2. Creamos una vista de modelo segura que todas las demás heredarán
class SecureModelView(ModelView):
    def is_accessible(self):
        # Verifica si el usuario está logueado como admin
        return session.get('admin_logged_in')

    def inaccessible_callback(self, name, **kwargs):
        # Redirige a la página de login de admin si no está autenticado
        return redirect(url_for('admin.login'))

# 3. Hacemos que nuestras vistas hereden de SecureModelView
class UserModelView(SecureModelView):
    form_columns = ('username', 'email', 'password', 'enrolled_courses')
    column_list = ('username', 'email')
    form_args = { 'enrolled_courses': { 'label': 'Cursos Inscritos' } }
    form_extra_fields = { 'password': PasswordField('Nueva Contraseña (dejar en blanco para no cambiar)') }
    column_exclude_list = ('password_hash',)
    form_excluded_columns = ('password_hash', 'created_at')

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        elif is_created:
            model.password_hash = bcrypt.generate_password_hash('defaultpassword').decode('utf-8')

class CourseModelView(SecureModelView):
    # --- LÍNEA MODIFICADA ---
    form_columns = ('title', 'description', 'image_url', 'instructor')
    form_args = { 'instructor': { 'label': 'Instructor', 'query_factory': lambda: db.session.query(User).all() } }
    form_widget_args = { 'description': { 'rows': 10, 'class': 'form-control' } }
    
class LessonModelView(SecureModelView):
    # El modelo de Lesson no tiene 'content_type', se asume video/pdf según el nombre de archivo
    form_columns = ('title', 'content', 'order', 'course')
    column_list = ('title', 'order', 'course')
    form_args = { 'course': { 'label': 'Curso', 'query_factory': lambda: db.session.query(Course).all() } }

# 4. Inicializamos Admin con nuestra vista de índice segura
admin_instance = Admin(name='AcademiaLMS', template_mode='bootstrap4', index_view=SecureAdminIndexView())

# 5. Añadimos las vistas seguras al panel de administración
admin_instance.add_view(UserModelView(User, db.session))
admin_instance.add_view(CourseModelView(Course, db.session))
admin_instance.add_view(LessonModelView(Lesson, db.session))
