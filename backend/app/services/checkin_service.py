from datetime import datetime, timezone

from ..core.errors import ApiError
from ..core.security import read_qr_token
from ..db.mongo import get_db, next_id, now_utc


class CheckinService:
    @staticmethod
    def _add_log(registration_id, admin_id, result, message):
        db = get_db()
        db.checkin_logs.insert_one(
            {
                "id": next_id("checkin_logs"),
                "registration_id": registration_id,
                "admin_id": admin_id,
                "result": result,
                "message": message,
                "scanned_at": now_utc(),
            }
        )

    @staticmethod
    def scan(admin_id, qr_token, expected_event_id=None):
        db = get_db()
        payload = read_qr_token(qr_token)
        if not payload:
            CheckinService._add_log(None, admin_id, "invalid_qr", "Invalid QR token")
            raise ApiError("Invalid QR token", 422)

        if expected_event_id is not None and payload.get("event_id") != expected_event_id:
            CheckinService._add_log(None, admin_id, "invalid_qr", "QR does not belong to this event")
            raise ApiError("This QR does not belong to the selected event", 422)

        registration = db.registrations.find_one({"id": payload.get("registration_id")})
        if not registration:
            raise ApiError("Registration not found", 404)

        if expected_event_id is not None and registration["event_id"] != expected_event_id:
            CheckinService._add_log(registration["id"], admin_id, "invalid_qr", "Registration does not belong to this event")
            raise ApiError("This registration is not for the selected event", 422)

        event = db.events.find_one({"id": registration["event_id"]})
        if not event or event.get("status") not in ["ongoing", "completed"]:
            raise ApiError("Event is not in check-in state", 409)

        if registration.get("status") == "checked_in":
            CheckinService._add_log(registration["id"], admin_id, "already_checked_in", "User is already checked in")
            return {"result": "already_checked_in", "registration": registration}

        checked_at = datetime.now(timezone.utc)
        db.registrations.update_one(
            {"id": registration["id"]},
            {
                "$set": {
                    "status": "checked_in",
                    "checked_in_at": checked_at,
                    "checked_in_by": admin_id,
                    "updated_at": now_utc(),
                }
            },
        )

        CheckinService._add_log(registration["id"], admin_id, "success", "Checked in successfully")
        registration["status"] = "checked_in"
        registration["checked_in_at"] = checked_at
        registration["checked_in_by"] = admin_id
        return {"result": "success", "registration": registration}

    @staticmethod
    def list_logs(event_id=None):
        db = get_db()
        if event_id is None:
            return list(db.checkin_logs.find().sort("scanned_at", -1).limit(200))

        registration_ids = [item["id"] for item in db.registrations.find({"event_id": event_id}, {"id": 1})]
        if not registration_ids:
            return []
        return list(db.checkin_logs.find({"registration_id": {"$in": registration_ids}}).sort("scanned_at", -1).limit(200))
