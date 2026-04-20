import json
from datetime import datetime

from ..core.errors import ApiError
from ..extensions import db
from ..models.models import Event, EventField


def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except Exception as exc:
        raise ApiError("Invalid datetime format. Use ISO format", 400) from exc


class EventService:
    @staticmethod
    def list_events(status=None):
        query = Event.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Event.event_date.asc()).all()

    @staticmethod
    def get_event(event_id):
        event = Event.query.get(event_id)
        if not event:
            raise ApiError("Event not found", 404)
        return event

    @staticmethod
    def create_event(payload, admin_id):
        event = Event(
            title=payload["title"],
            description=payload["description"],
            location=payload["location"],
            event_date=parse_datetime(payload["event_date"]),
            registration_deadline=parse_datetime(payload["registration_deadline"]) if payload.get("registration_deadline") else None,
            max_capacity=payload.get("max_capacity"),
            status=payload.get("status", "open"),
            created_by=admin_id,
        )
        db.session.add(event)
        db.session.flush()

        for index, field in enumerate(payload.get("fields", [])):
            event_field = EventField(
                event_id=event.id,
                field_name=field["field_name"],
                label=field["label"],
                field_type=field["field_type"],
                is_required=field.get("is_required", True),
                options_json=json.dumps(field.get("options", [])),
                regex_pattern=field.get("regex_pattern"),
                max_length=field.get("max_length"),
                display_order=index,
            )
            db.session.add(event_field)

        db.session.commit()
        return event

    @staticmethod
    def update_event(event_id, payload):
        event = EventService.get_event(event_id)

        for key in ["title", "description", "location", "max_capacity", "status"]:
            if key in payload:
                setattr(event, key, payload[key])

        if "event_date" in payload:
            event.event_date = parse_datetime(payload["event_date"])

        if "registration_deadline" in payload:
            event.registration_deadline = parse_datetime(payload["registration_deadline"]) if payload["registration_deadline"] else None

        if "fields" in payload:
            EventField.query.filter_by(event_id=event.id).delete()
            for index, field in enumerate(payload.get("fields", [])):
                db.session.add(
                    EventField(
                        event_id=event.id,
                        field_name=field["field_name"],
                        label=field["label"],
                        field_type=field["field_type"],
                        is_required=field.get("is_required", True),
                        options_json=json.dumps(field.get("options", [])),
                        regex_pattern=field.get("regex_pattern"),
                        max_length=field.get("max_length"),
                        display_order=index,
                    )
                )

        db.session.commit()
        return event

    @staticmethod
    def delete_event(event_id):
        event = EventService.get_event(event_id)
        db.session.delete(event)
        db.session.commit()

    @staticmethod
    def serialize_event(event, include_fields=False):
        payload = {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "location": event.location,
            "event_date": event.event_date.isoformat(),
            "registration_deadline": event.registration_deadline.isoformat() if event.registration_deadline else None,
            "max_capacity": event.max_capacity,
            "status": event.status,
        }

        if include_fields:
            fields = EventField.query.filter_by(event_id=event.id).order_by(EventField.display_order.asc()).all()
            payload["fields"] = [
                {
                    "id": item.id,
                    "field_name": item.field_name,
                    "label": item.label,
                    "field_type": item.field_type,
                    "is_required": item.is_required,
                    "options": json.loads(item.options_json or "[]"),
                    "regex_pattern": item.regex_pattern,
                    "max_length": item.max_length,
                    "display_order": item.display_order,
                }
                for item in fields
            ]

        return payload
