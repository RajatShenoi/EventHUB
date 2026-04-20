import json
import re

from ..core.errors import ApiError
from ..core.security import make_qr_token, qr_base64_from_token
from ..extensions import db
from ..models.models import Event, EventField, Registration, RegistrationFieldValue, User


class RegistrationService:
    @staticmethod
    def list_for_user(user_id):
        registrations = Registration.query.filter_by(user_id=user_id).all()
        return registrations

    @staticmethod
    def register_for_event(user_id, event_id, field_values):
        user = User.query.get(user_id)
        if not user:
            raise ApiError("User not found", 404)
        if user.role == "admin":
            raise ApiError("Admins cannot register for events", 403)

        event = Event.query.get(event_id)
        if not event:
            raise ApiError("Event not found", 404)
        if event.status not in ["open", "ongoing"]:
            raise ApiError("Event is not open for registration", 409)

        already = Registration.query.filter_by(user_id=user_id, event_id=event_id).first()
        if already:
            raise ApiError("Already registered for this event", 409)

        if event.max_capacity:
            total = Registration.query.filter_by(event_id=event_id).count()
            if total >= event.max_capacity:
                raise ApiError("Event is full", 409)

        fields = EventField.query.filter_by(event_id=event_id).all()

        for field in fields:
            value = field_values.get(field.field_name)
            if field.is_required and (value is None or str(value).strip() == ""):
                raise ApiError(f"{field.label} is required", 422)
            if value and field.max_length and len(str(value)) > field.max_length:
                raise ApiError(f"{field.label} exceeds max length", 422)
            if value and field.regex_pattern and not re.match(field.regex_pattern, str(value)):
                raise ApiError(f"{field.label} is invalid", 422)
            if value and field.field_type in ["select", "radio"]:
                allowed = json.loads(field.options_json or "[]")
                if allowed and str(value) not in allowed:
                    raise ApiError(f"{field.label} has an invalid option", 422)

        registration = Registration(user_id=user_id, event_id=event_id, status="registered")
        db.session.add(registration)
        db.session.flush()

        for field in fields:
            db.session.add(
                RegistrationFieldValue(
                    registration_id=registration.id,
                    event_field_id=field.id,
                    value=str(field_values.get(field.field_name, "")),
                )
            )

        token = make_qr_token({"registration_id": registration.id, "user_id": user_id, "event_id": event_id})
        registration.qr_token = token

        db.session.commit()

        return {
            "registration": registration,
            "qr_token": token,
            "qr_image": qr_base64_from_token(token),
        }

    @staticmethod
    def cancel_registration(user_id, registration_id):
        registration = Registration.query.get(registration_id)
        if not registration:
            raise ApiError("Registration not found", 404)
        if registration.user_id != user_id:
            raise ApiError("Forbidden", 403)
        if registration.status == "checked_in":
            raise ApiError("Cannot cancel after check-in", 409)

        db.session.delete(registration)
        db.session.commit()

    @staticmethod
    def update_registration(user_id, registration_id, field_values):
        registration = Registration.query.get(registration_id)
        if not registration:
            raise ApiError("Registration not found", 404)
        if registration.user_id != user_id:
            raise ApiError("Forbidden", 403)
        if registration.status == "checked_in":
            raise ApiError("Cannot edit after check-in", 409)

        values = RegistrationFieldValue.query.filter_by(registration_id=registration.id).all()
        fields = {item.event_field_id: EventField.query.get(item.event_field_id) for item in values}

        for item in values:
            field = fields.get(item.event_field_id)
            if field and field.field_name in field_values:
                item.value = str(field_values[field.field_name])

        db.session.commit()
        return registration

    @staticmethod
    def serialize_registration(registration):
        values = RegistrationFieldValue.query.filter_by(registration_id=registration.id).all()
        field_map = {}
        for value in values:
            field = EventField.query.get(value.event_field_id)
            if field:
                field_map[field.field_name] = value.value

        qr_image = qr_base64_from_token(registration.qr_token) if registration.qr_token else None

        return {
            "id": registration.id,
            "user_id": registration.user_id,
            "event_id": registration.event_id,
            "status": registration.status,
            "checked_in_at": registration.checked_in_at.isoformat() if registration.checked_in_at else None,
            "qr_token": registration.qr_token,
            "qr_image": qr_image,
            "field_values": field_map,
        }
