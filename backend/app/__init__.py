from flask import Flask

from .api.admin import admin_bp
from .api.auth import auth_bp
from .api.checkin import checkin_bp
from .api.events import events_bp
from .api.registrations import registrations_bp
from .api.results import results_bp
from .config import Config
from .core.errors import register_error_handlers
from .db.mongo import init_mongo
from .extensions import cors, jwt


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    init_mongo(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"].split(",")}})

    register_error_handlers(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(events_bp, url_prefix="/api/events")
    app.register_blueprint(registrations_bp, url_prefix="/api/registrations")
    app.register_blueprint(checkin_bp, url_prefix="/api/checkin")
    app.register_blueprint(results_bp, url_prefix="/api/results")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.get("/api/health")
    def health():
        return {"success": True, "message": "ok"}, 200

    return app
