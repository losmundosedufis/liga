from flask import Flask
from extensions import db, login_manager
from config import Config
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)

    from models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registrar Blueprints
    from routes.auth import auth_bp
    from routes.ligas import ligas_bp
    from routes.partidos import partidos_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(ligas_bp)
    app.register_blueprint(partidos_bp)

    return app

app = create_app()