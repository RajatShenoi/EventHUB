import json
import re

from ..core.errors import ApiError
from ..core.security import make_qr_token, qr_base64_from_token
from ..db.mongo import get_db, next_id, now_utc


class RegistrationService:
    @staticmethod
    def _validate_field_value(field, value):
        if field.get("is_required", True) and (value is None or str(value).strip() == ""):
            raise ApiError(f"{field['label']} is required", 422)
        if value and field.get("max_length") and len(str(value)) > field["max_length"]:
            raise ApiError(f"{field['label']} exceeds max length", 422)
        if value and field.get("regex_pattern") and not re.match(field["regex_pattern"], str(value)):
            raise ApiError(f"{field['label']} is invalid", 422)
        if value and field.get("field_type") in ["select", "radio"]:
            allowed = json.loads(field.get("options_json") or "[]")
            if allowed and str(value) not in allowed:
                raise ApiError(f"{field['label']} has an invalid option", 422)

    @staticmethod
    def _update_registration_fields(registration, field_values, allow_checked_in=False):
        if not isinstance(field_values, dict):
            raise ApiError("field_values must be an object", 400)
        if registration.get("status") == "checked_in" and not allow_checked_in:
            raise ApiError("Cannot edit after check-in", 409)

        db = get_db()
        fields = list(db.event_fields.find({"event_id": registration["event_id"]}))
        fields_by_name = {item["field_name"]: item for item in fields}

        for field_name in field_values:
            if field_name not in fields_by_name:
                raise ApiError(f"Unknown registration field: {field_name}", 422)

        existing_values = list(db.registration_field_values.find({"registration_id": registration["id"]}))
        values_by_field_id = {item["event_field_id"]: item for item in existing_values}

        now = now_utc()
        for field_name, value in field_values.items():
            field = fields_by_name[field_name]
            RegistrationService._validate_field_value(field, value)

            existing = values_by_field_id.get(field["id"])
            if existing:
                db.registration_field_values.update_one(
                    {"id": existing["id"]},
                    {"$set": {"value": str(value), "updated_at": now}},
                )
            else:
                db.registration_field_values.insert_one(
                    {
                        "id": next_id("registration_field_values"),
                        "registration_id": registration["id"],
                        "event_field_id": field["id"],
                        "value": str(value),
                        "created_at": now,
                        "updated_at": now,
                    }
                )

        db.registrations.update_one({"id": registration["id"]}, {"$set": {"updated_at": now}})
        return db.registrations.find_one({"id": registration["id"]})

    @staticmethod
    def list_for_user(user_id):
        db = get_db()
        return list(db.registrations.find({"user_id": user_id}))

    @staticmethod
    def register_for_event(user_id, event_id, field_values):
        db = get_db()

        user = db.users.find_one({"id": user_id})
        if not user:
            raise ApiError("User not found", 404)
        if user.get("role") == "admin":
            raise ApiError("Admins cannot register for events", 403)

        event = db.events.find_one({"id": event_id})
        if not event:
            raise ApiError("Event not found", 404)
        if event.get("status") not in ["open", "ongoing"]:
            raise ApiError("Event is not open for registration", 409)

        already = db.registrations.find_one({"user_id": user_id, "event_id": event_id})
        if already:
            raise ApiError("Already registered for this event", 409)

        if event.get("max_capacity"):
            total = db.registrations.count_documents({"event_id": event_id})
            if total >= event["max_capacity"]:
                raise ApiError("Event is full", 409)

        fields = list(db.event_fields.find({"event_id": event_id}))
        for field in fields:
            value = field_values.get(field["field_name"])
            RegistrationService._validate_field_value(field, value)

        now = now_utc()
        registration = {
            "id": next_id("registrations"),
            "user_id": user_id,
            "event_id": event_id,
            "status": "registered",
            "qr_token": None,
            "checked_in_at": None,
            "checked_in_by": None,
            "created_at": now,
            "updated_at": now,
        }
        db.registrations.insert_one(registration)

        field_value_docs = []
        for field in fields:
            field_value_docs.append(
                {
                    "id": next_id("registration_field_values"),
                    "registration_id": registration["id"],
                    "event_field_id": field["id"],
                    "value": str(field_values.get(field["field_name"], "")),
                    "created_at": now,
                    "updated_at": now,
                }
            )
        if field_value_docs:
            db.registration_field_values.insert_many(field_value_docs)

        token = make_qr_token({"registration_id": registration["id"], "user_id": user_id, "event_id": event_id})
        db.registrations.update_one({"id": registration["id"]}, {"$set": {"qr_token": token, "updated_at": now_utc()}})
        registration["qr_token"] = token

        return {
            "registration": registration,
            "qr_token": token,
            "qr_image": qr_base64_from_token(token),
        }

    @staticmethod
    def cancel_registration(user_id, registration_id):
        db = get_db()
        registration = db.registrations.find_one({"id": registration_id})
        if not registration:
            raise ApiError("Registration not found", 404)
        if registration["user_id"] != user_id:
            raise ApiError("Forbidden", 403)
        if registration.get("status") == "checked_in":
            raise ApiError("Cannot cancel after check-in", 409)

        db.registration_field_values.delete_many({"registration_id": registration_id})
        db.checkin_logs.delete_many({"registration_id": registration_id})
        db.event_results.delete_many({"event_id": registration["event_id"], "user_id": registration["user_id"]})
        db.registrations.delete_one({"id": registration_id})

    @staticmethod
    def update_registration(user_id, registration_id, field_values):
        db = get_db()
        registration = db.registrations.find_one({"id": registration_id})
        if not registration:
            raise ApiError("Registration not found", 404)
        if registration["user_id"] != user_id:
            raise ApiError("Forbidden", 403)
        return RegistrationService._update_registration_fields(registration, field_values, allow_checked_in=False)

    @staticmethod
    def admin_update_registration(registration_id, field_values):
        db = get_db()
        registration = db.registrations.find_one({"id": registration_id})
        if not registration:
            raise ApiError("Registration not found", 404)
        return RegistrationService._update_registration_fields(registration, field_values, allow_checked_in=True)

    @staticmethod
    def serialize_registration(registration):
        db = get_db()
        values = list(db.registration_field_values.find({"registration_id": registration["id"]}))
        field_ids = [item["event_field_id"] for item in values]
        field_docs = list(db.event_fields.find({"id": {"$in": field_ids}})) if field_ids else []
        field_map_by_id = {item["id"]: item for item in field_docs}

        field_map = {}
        for value in values:
            field = field_map_by_id.get(value["event_field_id"])
            if field:
                field_map[field["field_name"]] = value.get("value")

        qr_image = qr_base64_from_token(registration["qr_token"]) if registration.get("qr_token") else None

        return {
            "id": registration["id"],
            "user_id": registration["user_id"],
            "event_id": registration["event_id"],
            "status": registration.get("status"),
            "checked_in_at": registration["checked_in_at"].isoformat() if registration.get("checked_in_at") else None,
            "qr_token": registration.get("qr_token"),
            "qr_image": qr_image,
            "field_values": field_map,
        }
