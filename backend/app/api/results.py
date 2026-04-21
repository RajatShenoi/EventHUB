from flask import Blueprint, request
from flask_jwt_extended import get_jwt, get_jwt_identity

from ..core.decorators import role_required
from ..core.errors import ApiError
from ..db.mongo import get_db
from ..services.event_service import EventService
from ..services.result_service import ResultService

results_bp = Blueprint("results", __name__)


@results_bp.get("/event/<int:event_id>")
@role_required(["user", "admin"])
def get_event_results(event_id):
    role = get_jwt().get("role")
    current_user_id = int(get_jwt_identity())

    event = EventService.get_event(event_id)
    if event["status"] != "completed" and role != "admin":
        raise ApiError("Results are available after event completion", 403)

    rows, _ = ResultService.event_results(event_id)
    summary = ResultService.attendance_summary(event_id)
    user_ids = [item["user_id"] for item in rows]
    db = get_db()
    users = list(db.users.find({"id": {"$in": user_ids}})) if user_ids else []
    user_map = {user["id"]: user["full_name"] for user in users}

    ranking = []
    my_result = None
    for item in rows:
        row = {
            "user_id": item["user_id"],
            "full_name": user_map.get(item["user_id"]),
            "score": item["score"],
            "rank": item["rank"],
        }
        if role == "admin":
            row["remarks"] = item.get("remarks")
        ranking.append(row)

        if item["user_id"] == current_user_id:
            my_result = {
                "user_id": item["user_id"],
                "full_name": user_map.get(item["user_id"]),
                "score": item["score"],
                "rank": item["rank"],
                "remarks": item.get("remarks"),
            }

    response_data = {
        "ranking": ranking,
        "my_result": my_result,
    }

    if role == "admin":
        response_data["attendance"] = summary

    return {
        "success": True,
        "data": response_data,
    }


@results_bp.get("/event/<int:event_id>/registrations")
@role_required("admin")
def get_event_registrations(event_id):
    EventService.get_event(event_id)

    payload = ResultService.all_event_registrations_with_fields(event_id)
    return {"success": True, "data": payload}


@results_bp.get("/event/<int:event_id>/participants")
@role_required("admin")
def get_event_participants(event_id):
    EventService.get_event(event_id)

    payload = ResultService.event_participants_with_fields(event_id)
    return {"success": True, "data": payload}


@results_bp.post("/event/<int:event_id>/publish")
@role_required("admin")
def publish_event_results(event_id):
    EventService.get_event(event_id)

    payload = request.get_json() or {}
    entries = payload.get("scores", [])
    if not isinstance(entries, list):
        raise ApiError("scores must be a list", 400)

    published = ResultService.publish_scores(event_id, entries)
    return {"success": True, "data": {"published": published}}, 201


@results_bp.post("/event/<int:event_id>")
@role_required("admin")
def upsert_event_result(event_id):
    payload = request.get_json() or {}
    user_id = payload.get("user_id")
    score = payload.get("score")
    remarks = payload.get("remarks")
    if not all(value is not None for value in [user_id, score]):
        raise ApiError("user_id and score are required", 400)

    published = ResultService.publish_scores(
        event_id,
        [
            {
                "user_id": user_id,
                "score": score,
                "remarks": remarks,
            }
        ],
    )
    if not published:
        raise ApiError("Could not publish result for this participant", 400)

    result = published[0]
    return {
        "success": True,
        "data": {
            "event_id": event_id,
            "user_id": result["user_id"],
            "score": result["score"],
            "rank": result["rank"],
            "remarks": result["remarks"],
        },
    }, 201
