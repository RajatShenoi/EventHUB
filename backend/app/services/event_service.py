import json
from datetime import datetime

from ..core.errors import ApiError
from ..db.mongo import get_db, next_id, now_utc


def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except Exception as exc:
        raise ApiError("Invalid datetime format. Use ISO format", 400) from exc


class EventService:
    @staticmethod
    def list_events(status=None):
        db = get_db()
        query = {"status": status} if status else {}
        return list(db.events.find(query).sort("event_date", 1))

    @staticmethod
    def get_event(event_id):
        db = get_db()
        event = db.events.find_one({"id": event_id})
        if not event:
            raise ApiError("Event not found", 404)
        return event

    @staticmethod
    def create_event(payload, admin_id):
        db = get_db()
        now = now_utc()
        event = {
            "id": next_id("events"),
            "title": payload["title"],
            "description": payload["description"],
            "location": payload["location"],
            "event_date": parse_datetime(payload["event_date"]),
            "registration_deadline": parse_datetime(payload["registration_deadline"]) if payload.get("registration_deadline") else None,
            "max_capacity": payload.get("max_capacity"),
            "status": payload.get("status", "open"),
            "created_by": admin_id,
            "created_at": now,
            "updated_at": now,
        }
        db.events.insert_one(event)

        field_docs = []
        for index, field in enumerate(payload.get("fields", [])):
            field_docs.append(
                {
                    "id": next_id("event_fields"),
                    "event_id": event["id"],
                    "field_name": field["field_name"],
                    "label": field["label"],
                    "field_type": field["field_type"],
                    "is_required": field.get("is_required", True),
                    "options_json": json.dumps(field.get("options", [])),
                    "regex_pattern": field.get("regex_pattern"),
                    "max_length": field.get("max_length"),
                    "display_order": index,
                    "created_at": now,
                    "updated_at": now,
                }
            )
        if field_docs:
            db.event_fields.insert_many(field_docs)

        return event

    @staticmethod
    def update_event(event_id, payload):
        db = get_db()
        event = EventService.get_event(event_id)

        updates = {}
        for key in ["title", "description", "location", "max_capacity", "status"]:
            if key in payload:
                updates[key] = payload[key]

        if "event_date" in payload:
            updates["event_date"] = parse_datetime(payload["event_date"])

        if "registration_deadline" in payload:
            updates["registration_deadline"] = parse_datetime(payload["registration_deadline"]) if payload["registration_deadline"] else None

        if updates:
            updates["updated_at"] = now_utc()
            db.events.update_one({"id": event_id}, {"$set": updates})

        if "fields" in payload:
            old_field_ids = [item["id"] for item in db.event_fields.find({"event_id": event_id}, {"id": 1})]
            if old_field_ids:
                db.registration_field_values.delete_many({"event_field_id": {"$in": old_field_ids}})
            db.event_fields.delete_many({"event_id": event_id})

            now = now_utc()
            field_docs = []
            for index, field in enumerate(payload.get("fields", [])):
                field_docs.append(
                    {
                        "id": next_id("event_fields"),
                        "event_id": event_id,
                        "field_name": field["field_name"],
                        "label": field["label"],
                        "field_type": field["field_type"],
                        "is_required": field.get("is_required", True),
                        "options_json": json.dumps(field.get("options", [])),
                        "regex_pattern": field.get("regex_pattern"),
                        "max_length": field.get("max_length"),
                        "display_order": index,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
            if field_docs:
                db.event_fields.insert_many(field_docs)

        return EventService.get_event(event_id)

    @staticmethod
    def delete_event(event_id):
        db = get_db()
        EventService.get_event(event_id)

        field_ids = [item["id"] for item in db.event_fields.find({"event_id": event_id}, {"id": 1})]
        registration_ids = [item["id"] for item in db.registrations.find({"event_id": event_id}, {"id": 1})]

        if field_ids:
            db.registration_field_values.delete_many({"event_field_id": {"$in": field_ids}})
        if registration_ids:
            db.registration_field_values.delete_many({"registration_id": {"$in": registration_ids}})
            db.checkin_logs.delete_many({"registration_id": {"$in": registration_ids}})

        db.event_results.delete_many({"event_id": event_id})
        db.registrations.delete_many({"event_id": event_id})
        db.event_fields.delete_many({"event_id": event_id})
        db.events.delete_one({"id": event_id})

    @staticmethod
    def serialize_event(event, include_fields=False):
        payload = {
            "id": event["id"],
            "title": event["title"],
            "description": event["description"],
            "location": event["location"],
            "event_date": event["event_date"].isoformat(),
            "registration_deadline": event["registration_deadline"].isoformat() if event.get("registration_deadline") else None,
            "max_capacity": event.get("max_capacity"),
            "status": event["status"],
        }

        if include_fields:
            db = get_db()
            fields = list(db.event_fields.find({"event_id": event["id"]}).sort("display_order", 1))
            payload["fields"] = [
                {
                    "id": item["id"],
                    "field_name": item["field_name"],
                    "label": item["label"],
                    "field_type": item["field_type"],
                    "is_required": item.get("is_required", True),
                    "options": json.loads(item.get("options_json") or "[]"),
                    "regex_pattern": item.get("regex_pattern"),
                    "max_length": item.get("max_length"),
                    "display_order": item.get("display_order", 0),
                }
                for item in fields
            ]

        return payload
