from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.decorators import role_required
from ..core.errors import ApiError
from ..models.models import Registration
from ..services.registration_service import RegistrationService

registrations_bp = Blueprint("registrations", __name__)


@registrations_bp.post("")
@role_required("user")
def register_for_event():
    user_id = int(get_jwt_identity())
    payload = request.get_json() or {}
    event_id = payload.get("event_id")
    field_values = payload.get("field_values", {})

    if not event_id:
        raise ApiError("event_id is required", 400)

    result = RegistrationService.register_for_event(user_id, event_id, field_values)
    return {
        "success": True,
        "data": {
            "registration": RegistrationService.serialize_registration(result["registration"]),
            "qr_token": result["qr_token"],
            "qr_image": result["qr_image"],
        },
    }, 201


@registrations_bp.get("")
@role_required("user")
def list_registrations():
    user_id = int(get_jwt_identity())
    rows = RegistrationService.list_for_user(user_id)

    return {"success": True, "data": [RegistrationService.serialize_registration(item) for item in rows]}


@registrations_bp.put("/<int:registration_id>")
@role_required("user")
def update_registration(registration_id):
    user_id = int(get_jwt_identity())
    payload = request.get_json() or {}
    registration = RegistrationService.update_registration(user_id, registration_id, payload.get("field_values", {}))
    return {"success": True, "data": RegistrationService.serialize_registration(registration)}


@registrations_bp.delete("/<int:registration_id>")
@role_required("user")
def cancel_registration(registration_id):
    user_id = int(get_jwt_identity())
    RegistrationService.cancel_registration(user_id, registration_id)
    return {"success": True, "message": "Registration cancelled"}
