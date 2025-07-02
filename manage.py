## manage.py - Nuestro ÚNICO centro de comandos
import sys
from academy import create_app

# Creamos la instancia de la aplicación una sola vez
app = create_app()

# Leemos el comando desde la terminal. Si no hay comando, el defecto será 'runserver'
if len(sys.argv) > 1:
    command = sys.argv[1]
else:
    command = 'runserver' # Acción por defecto

# --- EJECUTOR DE COMANDOS ---

if command == 'runserver':
    print("-> Iniciando servidor de desarrollo en http://127.0.0.1:5000")
    # El debug=True hace que se reinicie solo al guardar cambios
    app.run(debug=True)

elif command in ['db_init', 'db_migrate', 'db_upgrade']:
    # Para los comandos de la base de datos, necesitamos el contexto de la aplicación
    with app.app_context():
        from flask_migrate import init as db_init, migrate as db_migrate, upgrade as db_upgrade

        if command == 'db_init':
            print("-> Inicializando...")
            db_init()
            print("¡Repositorio de migraciones creado!")

        elif command == 'db_migrate':
            print("-> Generando script de migración...")
            db_migrate(message="Nueva migración")
            print("¡Script de migración generado!")

        elif command == 'db_upgrade':
            print("-> Aplicando migración a la base de datos...")
            db_upgrade()
            print("¡Base de datos actualizada!")
else:
    print(f"Error: Comando '{command}' no reconocido.")
    print("Comandos disponibles: runserver, db_init, db_migrate, db_upgrade")