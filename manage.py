import sys
from academy import create_app

# 1. Creamos la instancia de la aplicación.
# Vercel importará este objeto 'app' para ejecutarlo en su propio servidor.
app = create_app()

# 2. Esta sección SÓLO se ejecuta cuando corres el comando "python manage.py ..."
# en tu propia computadora. Vercel ignorará este bloque por completo.
if __name__ == "__main__":
    # Leemos el comando desde la terminal.
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        # Si no se da un comando, por defecto se inicia el servidor de desarrollo.
        command = 'runserver'

    # --- EJECUTOR DE COMANDOS PARA DESARROLLO LOCAL ---

    if command == 'runserver':
        print("-> Iniciando servidor de desarrollo en http://127.0.0.1:5000")
        # Esta línea ahora solo se ejecuta en tu máquina, no en Vercel.
        app.run(debug=True)

    elif command in ['db_init', 'db_migrate', 'db_upgrade']:
        # Para los comandos de la base de datos, necesitamos el contexto de la aplicación.
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
