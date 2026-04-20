from functools import wraps

from flask_jwt_extended import get_jwt, jwt_required

from .errors import ApiError


def role_required(allowed_roles):
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def inner(*args, **kwargs):
            claims = get_jwt()
            role = claims.get("role")
            if role not in allowed_roles:
                raise ApiError("Forbidden", 403)
            return fn(*args, **kwargs)

        return inner

    return wrapper
