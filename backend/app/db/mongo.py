from datetime import datetime, timezone

from flask import current_app
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.errors import ConfigurationError


def now_utc():
    return datetime.now(timezone.utc)


def init_mongo(app):
    uri = app.config["MONGODB_URI"]
    default_db_name = app.config["MONGODB_DB_NAME"]

    if not uri:
        raise RuntimeError("MONGODB_URI is required. Set it to your MongoDB Atlas connection string.")

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db_name = default_db_name
    try:
        default_db = client.get_default_database()
        if default_db is not None:
            db_name = default_db.name
    except ConfigurationError:
        db_name = default_db_name

    try:
        client.admin.command("ping")
    except Exception as exc:
        raise RuntimeError(
            "Could not connect to MongoDB. Verify MONGODB_URI, Atlas IP access list, and credentials."
        ) from exc

    db = client[db_name]
    app.extensions["mongo_client"] = client
    app.extensions["mongo_db"] = db

    _ensure_indexes(db)


def get_db():
    return current_app.extensions["mongo_db"]


def next_id(counter_name):
    db = get_db()
    updated = db.counters.find_one_and_update(
        {"_id": counter_name},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(updated["value"])


def _ensure_indexes(db):
    db.users.create_index([("id", ASCENDING)], unique=True)
    db.users.create_index([("email", ASCENDING)], unique=True)

    db.events.create_index([("id", ASCENDING)], unique=True)
    db.events.create_index([("status", ASCENDING)])
    db.events.create_index([("event_date", ASCENDING)])

    db.event_fields.create_index([("id", ASCENDING)], unique=True)
    db.event_fields.create_index([("event_id", ASCENDING), ("display_order", ASCENDING)])

    db.registrations.create_index([("id", ASCENDING)], unique=True)
    db.registrations.create_index([("user_id", ASCENDING), ("event_id", ASCENDING)], unique=True)
    db.registrations.create_index([("event_id", ASCENDING), ("status", ASCENDING)])
    db.registrations.create_index([("qr_token", ASCENDING)], unique=True, sparse=True)

    db.registration_field_values.create_index([("id", ASCENDING)], unique=True)
    db.registration_field_values.create_index([("registration_id", ASCENDING), ("event_field_id", ASCENDING)], unique=True)

    db.checkin_logs.create_index([("id", ASCENDING)], unique=True)
    db.checkin_logs.create_index([("scanned_at", DESCENDING)])
    db.checkin_logs.create_index([("registration_id", ASCENDING), ("scanned_at", DESCENDING)])

    db.event_results.create_index([("id", ASCENDING)], unique=True)
    db.event_results.create_index([("event_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
    db.event_results.create_index([("event_id", ASCENDING), ("rank", ASCENDING)])

    db.admin_role_requests.create_index([("id", ASCENDING)], unique=True)
    db.admin_role_requests.create_index([("status", ASCENDING), ("created_at", DESCENDING)])
