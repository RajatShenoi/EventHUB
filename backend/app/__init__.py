import os
from flask import Flask
from sqlalchemy import event

from .api.admin import admin_bp
from .api.auth import auth_bp
from .api.checkin import checkin_bp
from .api.events import events_bp
from .api.registrations import registrations_bp
from .api.results import results_bp
from .config import Config
from .core.errors import register_error_handlers
from .extensions import cors, db, jwt


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"].split(",")}})

    register_error_handlers(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(events_bp, url_prefix="/api/events")
    app.register_blueprint(registrations_bp, url_prefix="/api/registrations")
    app.register_blueprint(checkin_bp, url_prefix="/api/checkin")
    app.register_blueprint(results_bp, url_prefix="/api/results")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    with app.app_context():
        @event.listens_for(db.engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        from . import models  # noqa: F401

        db.create_all()

    @app.get("/api/health")
    def health():
        return {"success": True, "message": "ok"}, 200

    return app
