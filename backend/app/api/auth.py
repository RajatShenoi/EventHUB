from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..core.errors import ApiError
from ..services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    for key in ["email", "full_name", "password"]:
        if not data.get(key):
            raise ApiError(f"{key} is required", 400)

    user = AuthService.register_user(data["email"].lower(), data["full_name"], data["password"])
    return {
        "success": True,
        "data": {"id": user["id"], "email": user["email"], "full_name": user["full_name"], "role": user["role"]},
    }, 201


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    for key in ["email", "password"]:
        if not data.get(key):
            raise ApiError(f"{key} is required", 400)

    user, token = AuthService.login(data["email"].lower(), data["password"])
    return {
        "success": True,
        "data": {
            "token": token,
            "user": {"id": user["id"], "email": user["email"], "full_name": user["full_name"], "role": user["role"]},
        },
    }


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = AuthService.get_user(user_id)

    return {
        "success": True,
        "data": {"id": user["id"], "email": user["email"], "full_name": user["full_name"], "role": user["role"]},
    }


@auth_bp.post("/request-admin")
@jwt_required()
def request_admin():
    raise ApiError("Users cannot request admin role. Admins must update roles from the Users page.", 403)
