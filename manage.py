import sys
from academy import create_app

# 1. Creamos la instancia de la aplicación.
#    Vercel importará este objeto 'app' para ejecutarlo.
app = create_app()

# 2. El código dentro de este bloque SÓLO se ejecutará cuando corras
#    "python manage.py ..." en tu propia computadora.
#    Vercel ignorará por completo todo lo que está aquí adentro.
if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = 'runserver'

    if command == 'runserver':
        print("-> Iniciando servidor de desarrollo en http://127.0.0.1:5000")
        app.run(debug=True)
    elif command in ['db_init', 'db_migrate', 'db_upgrade']:
        with app.app_context():
            from flask_migrate import init, migrate, upgrade
            if command == 'db_init':
                init()
            elif command == 'db_migrate':
                migrate(message="Nueva migración")
            elif command == 'db_upgrade':
                upgrade()
            print(f"Comando '{command}' ejecutado exitosamente.")
    else:
        print(f"Error: Comando '{command}' no reconocido.")

