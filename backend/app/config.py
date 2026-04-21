import os
from datetime import timedelta


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)


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
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "event_platform")
    JSON_SORT_KEYS = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")
