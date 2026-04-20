from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity

from ..core.decorators import role_required
from ..core.errors import ApiError
from ..extensions import db
from ..models.models import AdminRoleRequest, Event, Registration, User
from ..services.auth_service import AuthService

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/role-requests")
@role_required("admin")
def list_role_requests():
    requests = AuthService.list_all_requests()
    data = []
    for item in requests:
        user = User.query.get(item.user_id)
        reviewer = User.query.get(item.reviewed_by) if item.reviewed_by else None
        data.append(
            {
                "id": item.id,
                "user_id": item.user_id,
                "user_email": user.email if user else None,
                "user_full_name": user.full_name if user else None,
                "reason": item.reason,
                "status": item.status,
                "created_at": item.created_at.isoformat(),
                "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
                "reviewed_by": reviewer.email if reviewer else None,
            }
        )
    return {"success": True, "data": data}


@admin_bp.get("/users")
@role_required("admin")
def list_users():
    users = AuthService.list_users()
    data = []
    for user in users:
        registration_count = Registration.query.filter_by(user_id=user.id).count()
        checked_in_count = Registration.query.filter_by(user_id=user.id, status="checked_in").count()
        data.append(
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
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
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
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
        "data": {"id": user.id, "email": user.email},
    }


@admin_bp.post("/role-requests/<int:request_id>/review")
@role_required("admin")
def review_role_request(request_id):
    payload = request.get_json() or {}
    approve = bool(payload.get("approve", False))
    reviewed = AuthService.review_request(request_id, int(get_jwt_identity()), approve)
    return {
        "success": True,
        "data": {"id": reviewed.id, "status": reviewed.status, "user_id": reviewed.user_id},
    }


@admin_bp.post("/bootstrap")
def bootstrap_admin():
    data = request.get_json() or {}
    token = data.get("setup_token")
    if token != "LOCAL_SETUP_TOKEN":
        return {"success": False, "message": "Invalid setup token"}, 403

    email = data.get("email", "admin@local.dev")
    password = data.get("password", "Admin@1234")
    full_name = data.get("full_name", "Platform Admin")

    user = User.query.filter_by(email=email).first()
    if user:
        user.role = "admin"
        return {"success": True, "message": "Admin already exists and role ensured"}

    from ..core.security import hash_password
    from ..extensions import db

    admin = User(email=email, full_name=full_name, password_hash=hash_password(password), role="admin")
    db.session.add(admin)
    db.session.commit()
    return {"success": True, "message": "Admin created"}, 201
