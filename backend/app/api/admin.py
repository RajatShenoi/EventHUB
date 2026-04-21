from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity

from ..core.decorators import role_required
from ..core.errors import ApiError
from ..core.security import hash_password
from ..db.mongo import get_db, next_id, now_utc
from ..services.auth_service import AuthService

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/role-requests")
@role_required("admin")
def list_role_requests():
    db = get_db()
    requests = AuthService.list_all_requests()
    data = []
    for item in requests:
        user = db.users.find_one({"id": item["user_id"]})
        reviewer = db.users.find_one({"id": item.get("reviewed_by")}) if item.get("reviewed_by") else None
        data.append(
            {
                "id": item["id"],
                "user_id": item["user_id"],
                "user_email": user["email"] if user else None,
                "user_full_name": user["full_name"] if user else None,
                "reason": item.get("reason"),
                "status": item.get("status"),
                "created_at": item["created_at"].isoformat(),
                "reviewed_at": item["reviewed_at"].isoformat() if item.get("reviewed_at") else None,
                "reviewed_by": reviewer["email"] if reviewer else None,
            }
        )
    return {"success": True, "data": data}


@admin_bp.get("/users")
@role_required("admin")
def list_users():
    db = get_db()
    users = AuthService.list_users()
    data = []
    for user in users:
        registration_count = db.registrations.count_documents({"user_id": user["id"]})
        checked_in_count = db.registrations.count_documents({"user_id": user["id"], "status": "checked_in"})
        data.append(
            {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "created_at": user["created_at"].isoformat(),
                "registration_count": registration_count,
                "checked_in_count": checked_in_count,
            }
        )
    return {"success": True, "data": data}


@admin_bp.put("/users/<int:user_id>")
@role_required("admin")
def update_user(user_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id == user_id:
        raise ApiError("You cannot edit your own account here", 403)

    payload = request.get_json() or {}
    user = AuthService.update_user(user_id, payload)
    return {
        "success": True,
        "data": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "created_at": user["created_at"].isoformat(),
        },
    }


@admin_bp.delete("/users/<int:user_id>")
@role_required("admin")
def delete_user(user_id):
    current_user_id = int(get_jwt_identity())
    if current_user_id == user_id:
        raise ApiError("You cannot delete your own account here", 403)

    user = AuthService.delete_user(user_id)
    return {
        "success": True,
        "data": {"id": user["id"], "email": user["email"]},
    }


@admin_bp.post("/role-requests/<int:request_id>/review")
@role_required("admin")
def review_role_request(request_id):
    payload = request.get_json() or {}
    approve = bool(payload.get("approve", False))
    reviewed = AuthService.review_request(request_id, int(get_jwt_identity()), approve)
    return {
        "success": True,
        "data": {"id": reviewed["id"], "status": reviewed["status"], "user_id": reviewed["user_id"]},
    }


@admin_bp.post("/bootstrap")
def bootstrap_admin():
    db = get_db()
    data = request.get_json() or {}
    token = data.get("setup_token")
    if token != "LOCAL_SETUP_TOKEN":
        return {"success": False, "message": "Invalid setup token"}, 403

    email = data.get("email", "admin@local.dev")
    password = data.get("password", "Admin@1234")
    full_name = data.get("full_name", "Platform Admin")

    user = db.users.find_one({"email": email})
    if user:
        db.users.update_one({"id": user["id"]}, {"$set": {"role": "admin", "updated_at": now_utc()}})
        return {"success": True, "message": "Admin already exists and role ensured"}

    now = now_utc()
    admin = {
        "id": next_id("users"),
        "email": email,
        "full_name": full_name,
        "password_hash": hash_password(password),
        "role": "admin",
        "created_at": now,
        "updated_at": now,
    }
    db.users.insert_one(admin)
    return {"success": True, "message": "Admin created"}, 201
