from flask import Blueprint, request
from flask_jwt_extended import get_jwt

from ..core.decorators import role_required
from ..core.errors import ApiError
from ..models.models import Event, EventResult
from ..services.result_service import ResultService

results_bp = Blueprint("results", __name__)


@results_bp.get("/event/<int:event_id>")
@role_required(["user", "admin"])
def get_event_results(event_id):
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", 404)
    if event.status != "completed" and get_jwt().get("role") != "admin":
        raise ApiError("Results are available after event completion", 403)

    rows, _ = ResultService.event_results(event_id)
    summary = ResultService.attendance_summary(event_id)

    return {
        "success": True,
        "data": {
            "attendance": summary,
            "ranking": [
                {"user_id": item.user_id, "score": item.score, "rank": item.rank, "remarks": item.remarks}
                for item in rows
            ],
        },
    }


@results_bp.post("/event/<int:event_id>")
@role_required("admin")
def upsert_event_result(event_id):
    payload = request.get_json() or {}
    user_id = payload.get("user_id")
    score = payload.get("score")
    rank = payload.get("rank")
    remarks = payload.get("remarks")
    if not all(value is not None for value in [user_id, score, rank]):
        raise ApiError("user_id, score and rank are required", 400)

    result = ResultService.upsert_result(event_id, user_id, score, rank, remarks)
    return {
        "success": True,
        "data": {
            "id": result.id,
            "event_id": result.event_id,
            "user_id": result.user_id,
            "score": result.score,
            "rank": result.rank,
            "remarks": result.remarks,
        },
    }, 201
