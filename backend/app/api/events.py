from flask import Blueprint, request

from ..core.decorators import role_required
from ..services.event_service import EventService

events_bp = Blueprint("events", __name__)


@events_bp.get("")
def list_events():
    status = request.args.get("status")
    rows = EventService.list_events(status)
    return {"success": True, "data": [EventService.serialize_event(item) for item in rows]}


@events_bp.get("/<int:event_id>")
def get_event(event_id):
    event = EventService.get_event(event_id)
    return {"success": True, "data": EventService.serialize_event(event, include_fields=True)}


@events_bp.post("")
@role_required("admin")
def create_event():
    from flask_jwt_extended import get_jwt_identity

    payload = request.get_json() or {}
    event = EventService.create_event(payload, int(get_jwt_identity()))
    return {"success": True, "data": EventService.serialize_event(event, include_fields=True)}, 201


@events_bp.put("/<int:event_id>")
@role_required("admin")
def update_event(event_id):
    payload = request.get_json() or {}
    event = EventService.update_event(event_id, payload)
    return {"success": True, "data": EventService.serialize_event(event, include_fields=True)}


@events_bp.delete("/<int:event_id>")
@role_required("admin")
def delete_event(event_id):
    EventService.delete_event(event_id)
    return {"success": True, "message": "Deleted"}
