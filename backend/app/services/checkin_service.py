from datetime import datetime, timezone

from ..core.errors import ApiError
from ..core.security import read_qr_token
from ..extensions import db
from ..models.models import CheckinLog, Event, Registration


class CheckinService:
    @staticmethod
    def scan(admin_id, qr_token):
        payload = read_qr_token(qr_token)
        if not payload:
            log = CheckinLog(registration_id=0, admin_id=admin_id, result="invalid_qr", message="Invalid QR token")
            db.session.add(log)
            db.session.commit()
            raise ApiError("Invalid QR token", 422)

        registration = Registration.query.get(payload.get("registration_id"))
        if not registration:
            raise ApiError("Registration not found", 404)

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
    def list_logs():
        return CheckinLog.query.order_by(CheckinLog.scanned_at.desc()).limit(200).all()
