from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity

from ..core.decorators import role_required
from ..services.checkin_service import CheckinService
from ..services.registration_service import RegistrationService

checkin_bp = Blueprint("checkin", __name__)


@checkin_bp.post("/scan")
@role_required("admin")
def scan_qr():
    admin_id = int(get_jwt_identity())
    data = request.get_json() or {}
    qr_token = data.get("qr_token")
    event_id = data.get("event_id")

    if event_id is not None:
        try:
            event_id = int(event_id)
        except (TypeError, ValueError):
            return {"success": False, "message": "event_id must be a valid integer"}, 400

    result = CheckinService.scan(admin_id, qr_token, event_id)
    return {
        "success": True,
        "data": {
            "result": result["result"],
            "registration": RegistrationService.serialize_registration(result["registration"]),
        },
    }


@checkin_bp.get("/history")
@role_required("admin")
def history():
    event_id = request.args.get("event_id")
    if event_id is not None:
        try:
            event_id = int(event_id)
        except (TypeError, ValueError):
            return {"success": False, "message": "event_id must be a valid integer"}, 400

    logs = CheckinService.list_logs(event_id)
    return {
        "success": True,
        "data": [
            {
                "id": item.id,
                "registration_id": item.registration_id,
                "admin_id": item.admin_id,
                "result": item.result,
                "message": item.message,
                "scanned_at": item.scanned_at.isoformat(),
            }
            for item in logs
        ],
    }
