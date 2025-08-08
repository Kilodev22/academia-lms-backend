# academy/routes.py

# --- IMPORTS ---
import sys
import traceback
import locale
from datetime import datetime
from flask import render_template, send_from_directory, current_app, request, Response, abort, jsonify
import os
import re
from flask import Blueprint
from .extensions import db, bcrypt, oauth

from .models import User, Course, Lesson
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity,decode_token
from .extensions import jwt
from sqlalchemy import or_ # <-- AÑADE ESTE IMPORT AL INICIO DEL ARCHIVO
from flask import url_for, redirect, session



#from weasyprint import HTML, CSS

# --- CONFIGURACIÓN DE IDIOMA PARA LA FECHA ---
try:
    locale.setlocale(locale.LC_TIME, 'es_CO.UTF-8')
except locale.Error:
    try:
        # Opción de fallback para sistemas Windows
        locale.setlocale(locale.LC_TIME, 'Spanish_Colombia')
    except locale.Error:
        # Si todo falla, usa el locale por defecto del sistema y registra un aviso
        print("Advertencia: No se pudo establecer el locale a 'es_CO.UTF-8'. Las fechas podrían no mostrarse en español.")
        pass # La aplicación continuará ejecutándose con el idioma por defecto del sistema
    

main_routes = Blueprint('main', __name__)

# ===================================================================
# CALLBACK DE LISTA NEGRA/REVOCACIÓN DE TOKENS JWT
# Esta función se llama cada vez que se accede a un endpoint protegido
# para verificar si el JTI del token es válido para el usuario actual. [cite: 266, 347, 567, 690, 913]
# ===================================================================

# ...
from datetime import datetime, timedelta

# ...

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    user_id = jwt_payload.get('sub')
    jti = jwt_payload.get('jti')

    # === 1. FORZAR LECTURA CONSISTENTE (PRIMERA LÍNEA DE DEFENSA) ===
    db.session.expire_all() # Limpia la caché de la sesión
    user = db.session.query(User).get(user_id) # Vuelve a consultar al usuario de la DB

    # === 2. LÓGICA DEL PERÍODO DE GRACIA (PARCHE PARA INCONSISTENCIA DE REPLICACIÓN) ===
    issued_at_timestamp = jwt_payload.get('iat') # Obtiene el timestamp de emisión del token
    
    # Solo aplica el período de gracia si tenemos un timestamp de emisión
    if issued_at_timestamp:
        issued_at_datetime = datetime.fromtimestamp(issued_at_timestamp)
        GRACE_PERIOD = timedelta(seconds=10) # Define un período de gracia (ej. 5 segundos)

        # Si el token fue emitido muy recientemente...
        if (datetime.utcnow() - issued_at_datetime) < GRACE_PERIOD:
            # ...y el usuario existe, y el JTI del token *coincide* con el last_jti en la DB
            # (que debería haber sido escrito justo antes de esto)
            if user and user.last_jti == jti:
               
                return False # ¡IMPORTANTE: NO revocar! Permitir el paso.

    # === 3. Lógica de revocación normal (si no aplica el período de gracia o no coincide) ===
    print(f"Verificando token para user_id: {user_id}, JTI: {jti}")
    if user is None:
        print(f"Usuario {user_id} no encontrado. Token revocado.")
        return True # Si el usuario no existe, revocar

    is_revoked = user.last_jti != jti # Comparación final: JTI del token vs last_jti de la DB
    print(f"last_jti almacenado: {user.last_jti}, JTI del token actual: {jti}, Revocado: {is_revoked}")
    return is_revoked
# --- RUTAS DE AUTENTICACIÓN Y GENERALES (SIN CAMBIOS) ---

@main_routes.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    user_exists = User.query.filter_by(username=data['username']).first()
    email_exists = User.query.filter_by(email=data['email']).first()
    if user_exists or email_exists:
        return jsonify({'message': 'El nombre de usuario o el correo ya existen'}), 409
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Usuario creado exitosamente'}), 201

@main_routes.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email', None)
    password = data.get('password', None)
    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=str(user.id))

        try:
            decoded_token = decode_token(access_token)
            new_jti = decoded_token['jti']
        except Exception as e:
            print(f"ERROR al decodificar token o obtener JTI: {e}")
            return jsonify({"message": "Error interno al generar sesión"}), 500

        user.last_jti = new_jti
        db.session.add(user) 
        db.session.commit() # Asegúrate de que el commit se haga aquí
        print(f"LOGIN: JTI {new_jti} asignado y commiteado para user_id: {user.id}. last_jti en DB: {user.last_jti}")

        return jsonify(access_token=access_token), 200
    return jsonify({"message": "Credenciales inválidas"}), 401

@main_routes.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "Usuario no encontrado"}), 404
    return jsonify({ "id": user.id, "username": user.username, "email": user.email, "member_since": user.created_at.strftime("%Y-%m-%d %H:%M:%S") }), 200

# --- RUTAS DE CURSOS (CON LA CORRECCIÓN APLICADA) ---

@main_routes.route('/courses', methods=['POST'])
@jwt_required()
def create_course():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    if not title:
        return jsonify({"message": "El título es obligatorio"}), 400
    new_course = Course(title=title, description=description, instructor_id=current_user_id)
    db.session.add(new_course)
    db.session.commit()
    return jsonify({ "id": new_course.id, "title": new_course.title, "description": new_course.description, "instructor_id": int(new_course.instructor_id) }), 201

@main_routes.route('/courses', methods=['GET'])

def get_all_courses():
    # 1. Obtiene el término de búsqueda de los parámetros de la URL
    search_term = request.args.get('search', None)
    
    # 2. Inicia la consulta base
    query = Course.query

    # 3. Si hay un término de búsqueda, filtra la consulta
    if search_term:
        search_pattern = f"%{search_term}%"
        # Filtra por título O descripción (insensible a mayúsculas/minúsculas)
        query = query.filter(or_(
            Course.title.ilike(search_pattern),
            Course.description.ilike(search_pattern)
        ))

    # 4. Ejecuta la consulta final
    courses = query.all()
    
    # El resto de la función permanece igual
    results = [{"id": course.id, "title": course.title, "description": course.description, "instructor_id": course.instructor_id, "image_url": course.image_url} for course in courses]
    return jsonify(results), 200

@main_routes.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"message": "Curso no encontrado"}), 404
    # --- LÍNEA MODIFICADA ---
    return jsonify({"id": course.id, "title": course.title, "description": course.description, "instructor_id": course.instructor_id, "created_at": course.created_at.strftime("%Y-%m-%d %H:%M:%S"), "image_url": course.image_url}), 200

@main_routes.route('/courses/<int:course_id>/lessons', methods=['POST'])
@jwt_required()
def create_lesson_for_course(course_id):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"message": "Curso no encontrado"}), 404
    current_user_id = get_jwt_identity()
    if str(course.instructor_id) != current_user_id:
        return jsonify({"message": "No tienes permiso para añadir lecciones a este curso"}), 403
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    order = data.get('order')
    if not title or not content or order is None:
        return jsonify({"message": "Título, contenido y orden son obligatorios"}), 400
    new_lesson = Lesson(title=title, content=content, order=order, course_id=course.id)
    db.session.add(new_lesson)
    db.session.commit()
    return jsonify({"message": f"Lección '{new_lesson.title}' creada exitosamente en el curso '{course.title}'"}), 201


# ===================================================================
# FUNCIÓN MODIFICADA PARA SOPORTAR TIPOS DE CONTENIDO
# ===================================================================
@main_routes.route('/courses/<int:course_id>/lessons', methods=['GET'])
@jwt_required()
def get_lessons_for_course(course_id):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"message": "Curso no encontrado"}), 404
    
    lessons = sorted(course.lessons, key=lambda lesson: lesson.order)
    
    results = []
    for lesson in lessons:
        content_type = 'text' # Valor por defecto
        if lesson.content:
            filename = lesson.content.lower()
            if filename.endswith(('.mp4', '.mov', '.avi', '.webm')):
                content_type = 'video'
            elif filename.endswith('.pdf'):
                content_type = 'pdf'
            elif filename.endswith(('.html', '.htm')):
                content_type = 'html'
            # --- LÍNEA AÑADIDA ---
            elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
                content_type = 'image'
        
        results.append({
            "id": lesson.id, 
            "title": lesson.title, 
            "order": lesson.order,
            "content": lesson.content,
            "content_type": content_type  # AHORA ENVIARÁ 'image' CORRECTAMENTE
        })
    
    return jsonify(results), 200


@main_routes.route('/my-courses', methods=['GET'])
@jwt_required()
def get_my_courses():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    enrolled_courses = user.enrolled_courses
    # --- LÍNEA MODIFICADA ---
    results = [{"id": course.id, "title": course.title, "description": course.description, "image_url": course.image_url} for course in enrolled_courses]
    return jsonify(results), 200

#@main_routes.route('/courses/<int:course_id>/certificate', methods=['GET'])
#@jwt_required()###
##   current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "Usuario no encontrado"}), 404
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"message": "Curso no encontrado"}), 404
    if course not in user.enrolled_courses:
        return jsonify({"message": "No estás inscrito en este curso"}), 403
    issue_date = datetime.now().strftime("%d de %B de %Y")
    rendered_html = render_template('certificate_template.html', student_name=user.username, course_name=course.title, issue_date=issue_date)
    pdf = HTML(string=rendered_html).write_pdf()
#  return Response(pdf, mimetype='application/pdf', headers={'Content-Disposition': 'attachment;filename=certificado.pdf'})
##

# --- RUTAS DE ARCHIVOS ---
@main_routes.route('/videos/<path:filename>')
def serve_video(filename):
    video_dir = os.path.join(current_app.root_path, 'static', 'videos')
    video_path = os.path.join(video_dir, filename)
    if not os.path.isfile(video_path):
        abort(404)
    file_size = os.path.getsize(video_path)
    range_header = request.headers.get('Range', None)
    if not range_header:
        rv = Response(status=200, mimetype='video/mp4')
        rv.headers.add('Content-Length', str(file_size))
        rv.headers.add('Accept-Ranges', 'bytes')
        return rv
    start_byte, end_byte = 0, None
    range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
    if range_match:
        start_byte = int(range_match.group(1))
        if range_match.group(2):
            end_byte = int(range_match.group(2))
    if end_byte is None or end_byte > file_size - 1:
        end_byte = file_size - 1
    content_length = end_byte - start_byte + 1
    def generate_chunks():
        with open(video_path, 'rb') as f:
            f.seek(start_byte)
            bytes_to_read = content_length
            while bytes_to_read > 0:
                chunk = f.read(min(1024 * 512, bytes_to_read))
                if not chunk: break
                bytes_to_read -= len(chunk)
                yield chunk
    response = Response(generate_chunks(), 206, mimetype='video/mp4', direct_passthrough=True)
    response.headers.add('Content-Range', f'bytes {start_byte}-{end_byte}/{file_size}')
    response.headers.add('Accept-Ranges', 'bytes')
    response.headers.add('Content-Length', str(content_length))
    return response

# ===================================================================
# NUEVA RUTA PARA SERVIR DOCUMENTOS ESTÁTICOS (PDFs, etc.)
# ===================================================================
@main_routes.route('/documents/<path:filename>')
def serve_document(filename):
    """
    Esta función sirve archivos estáticos como PDFs.
    Asegúrate de tener una carpeta 'documents' dentro de 'static'.
    """
    docs_dir = os.path.join(current_app.root_path, 'static', 'documents')
    return send_from_directory(docs_dir, filename)

# ===================================================================
# NUEVAS RUTAS PARA EL LOGIN CON GOOGLE
# ===================================================================

@main_routes.route('/login/google')
def google_login():
    """
    Ruta para iniciar el flujo de autenticación con Google.
    Redirige al usuario a la página de consentimiento de Google.
    """
    # Construye la URL de callback que Google usará para devolver al usuario.
    # Debe coincidir exactamente con la que configuraste en la Consola de Google.
    redirect_uri = url_for('main.google_authorize', _external=True)
    print(f"DEBUG: Generated Redirect URI is: {redirect_uri}")
    # Usa la librería oauth para generar y redirigir a la URL de autorización de Google.
    return oauth.google.authorize_redirect(redirect_uri)


# academy/routes.py

# academy/routes.py

@main_routes.route('/auth/google/callback')
def google_authorize():
    try:
        token = oauth.google.authorize_access_token()
        nonce = session.get('google_nonce')
        user_info = oauth.google.parse_id_token(token, nonce=nonce)

        email = user_info.get('email')
        username = user_info.get('name')
        user = User.query.filter_by(email=email).first()

        if not user:
            user = User(
                email=email,
                username=username,
                password_hash='social_login'
            )
            # Nota: No necesitamos db.session.add(user) aquí todavía
            # lo haremos junto con la actualización del JTI.
        
        access_token = create_access_token(identity=str(user.id))
        
        # --- ¡AQUÍ ESTÁ LA SOLUCIÓN! ---
        # 1. Decodificamos el token recién creado para obtener su JTI (ID único).
        try:
            decoded_token = decode_token(access_token)
            new_jti = decoded_token['jti']
        except Exception as e:
            print(f"ERROR al decodificar token o obtener JTI: {e}")
            return jsonify({"message": "Error interno al generar sesión"}), 500

        # 2. Asignamos el nuevo JTI al usuario y guardamos en la base de datos.
        user.last_jti = new_jti
        db.session.add(user) 
        db.session.commit()
        # --- FIN DE LA SOLUCIÓN ---

        frontend_url = current_app.config.get('FRONTEND_URL')
        redirect_url = f'{frontend_url}/plataforma.html#access_token={access_token}'
        
        return redirect(redirect_url)

    except Exception as e:
        print("---!!! OAUTH ERROR DETECTADO !!! ---")
        print(f"La excepción fue: {e}")
        import traceback
        traceback.print_exc()
        print("---!!! FIN DEL REPORTE DE ERROR !!! ---")
        return redirect(f"{current_app.config.get('FRONTEND_URL')}/index.html?error=google_auth_failed")