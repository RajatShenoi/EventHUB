from datetime import datetime, timezone

from ..core.errors import ApiError
from ..core.security import read_qr_token
from ..extensions import db
from ..models.models import CheckinLog, Event, Registration


class CheckinService:
    @staticmethod
    def scan(admin_id, qr_token, expected_event_id=None):
        payload = read_qr_token(qr_token)
        if not payload:
            log = CheckinLog(registration_id=None, admin_id=admin_id, result="invalid_qr", message="Invalid QR token")
            db.session.add(log)
            db.session.commit()
            raise ApiError("Invalid QR token", 422)

        if expected_event_id is not None and payload.get("event_id") != expected_event_id:
            db.session.add(
                CheckinLog(
                    registration_id=None,
                    admin_id=admin_id,
                    result="invalid_qr",
                    message="QR does not belong to this event",
                )
            )
            db.session.commit()
            raise ApiError("This QR does not belong to the selected event", 422)

        registration = Registration.query.get(payload.get("registration_id"))
        if not registration:
            raise ApiError("Registration not found", 404)

        if expected_event_id is not None and registration.event_id != expected_event_id:
            db.session.add(
                CheckinLog(
                    registration_id=registration.id,
                    admin_id=admin_id,
                    result="invalid_qr",
                    message="Registration does not belong to this event",
                )
            )
            db.session.commit()
            raise ApiError("This registration is not for the selected event", 422)

        event = Event.query.get(registration.event_id)
        if not event or event.status not in ["ongoing", "completed"]:
            raise ApiError("Event is not in check-in state", 409)

        if registration.status == "checked_in":
            db.session.add(
                CheckinLog(
                    registration_id=registration.id,
                    admin_id=admin_id,
                    result="already_checked_in",
                    message="User is already checked in",
                )
            )
            db.session.commit()
            return {"result": "already_checked_in", "registration": registration}

        registration.status = "checked_in"
        registration.checked_in_at = datetime.now(timezone.utc)
        registration.checked_in_by = admin_id

        db.session.add(
            CheckinLog(
                registration_id=registration.id,
                admin_id=admin_id,
                result="success",
                message="Checked in successfully",
            )
        )
        db.session.commit()

        return {"result": "success", "registration": registration}

    @staticmethod
    def list_logs(event_id=None):
        query = CheckinLog.query
        if event_id is not None:
            query = query.join(Registration, CheckinLog.registration_id == Registration.id).filter(Registration.event_id == event_id)

        return query.order_by(CheckinLog.scanned_at.desc()).limit(200).all()
