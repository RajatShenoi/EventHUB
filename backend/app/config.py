import os
from datetime import timedelta


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DEFAULT_SQLITE_PATH = os.path.join(INSTANCE_DIR, "app.db")


def _normalized_database_uri():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return f"sqlite:///{DEFAULT_SQLITE_PATH}"

    if database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:////"):
        relative_path = database_url.replace("sqlite:///", "", 1)
        absolute_path = os.path.abspath(os.path.join(BASE_DIR, relative_path))
        parent_dir = os.path.dirname(absolute_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        return f"sqlite:///{absolute_path}"

    return database_url


def _secret_value(name, fallback):
    value = os.getenv(name)
    if not value:
        return fallback

    if len(value.encode("utf-8")) < 32:
        return fallback

    return value


class Config:
    SECRET_KEY = _secret_value("SECRET_KEY", "dev-secret-key-change-this-before-production-2026")
    JWT_SECRET_KEY = _secret_value("JWT_SECRET_KEY", "dev-jwt-secret-key-change-this-before-production-2026")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    SQLALCHEMY_DATABASE_URI = _normalized_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")
