from flask_jwt_extended import create_access_token

from ..core.errors import ApiError
from ..core.security import hash_password, verify_password
from ..db.mongo import get_db, next_id, now_utc


class AuthService:
    @staticmethod
    def register_user(email, full_name, password):
        db = get_db()
        if db.users.find_one({"email": email}):
            raise ApiError("Email already exists", 409)

        user = {
            "id": next_id("users"),
            "email": email,
            "full_name": full_name,
            "password_hash": hash_password(password),
            "role": "user",
            "created_at": now_utc(),
            "updated_at": now_utc(),
        }
        db.users.insert_one(user)
        return user

    @staticmethod
    def login(email, password):
        db = get_db()
        user = db.users.find_one({"email": email})
        if not user or not verify_password(password, user["password_hash"]):
            raise ApiError("Invalid credentials", 401)

        token = create_access_token(identity=str(user["id"]), additional_claims={"role": user["role"]})
        return user, token

    @staticmethod
    def list_pending_requests():
        db = get_db()
        return list(db.admin_role_requests.find({"status": "pending"}).sort("created_at", -1))

    @staticmethod
    def list_all_requests():
        db = get_db()
        return list(db.admin_role_requests.find().sort("created_at", -1))

    @staticmethod
    def list_users():
        db = get_db()
        return list(db.users.find().sort("created_at", -1))

    @staticmethod
    def get_user(user_id):
        db = get_db()
        user = db.users.find_one({"id": user_id})
        if not user:
            raise ApiError("User not found", 404)
        return user

    @staticmethod
    def update_user(user_id, payload):
        db = get_db()
        user = AuthService.get_user(user_id)

        email = payload.get("email")
        full_name = payload.get("full_name")
        role = payload.get("role")

        updates = {}
        if email and email.lower() != user["email"]:
            existing = db.users.find_one({"email": email.lower(), "id": {"$ne": user_id}})
            if existing:
                raise ApiError("Email already exists", 409)
            updates["email"] = email.lower()

        if full_name:
            updates["full_name"] = full_name

        if role in {"user", "admin"}:
            updates["role"] = role

        if updates:
            updates["updated_at"] = now_utc()
            db.users.update_one({"id": user_id}, {"$set": updates})
            user = db.users.find_one({"id": user_id})

        return user

    @staticmethod
    def delete_user(user_id):
        db = get_db()
        user = AuthService.get_user(user_id)

        created_event_ids = [item["id"] for item in db.events.find({"created_by": user_id}, {"id": 1})]
        user_registration_ids = [item["id"] for item in db.registrations.find({"user_id": user_id}, {"id": 1})]

        if created_event_ids:
            event_field_ids = [item["id"] for item in db.event_fields.find({"event_id": {"$in": created_event_ids}}, {"id": 1})]
            event_registration_ids = [item["id"] for item in db.registrations.find({"event_id": {"$in": created_event_ids}}, {"id": 1})]

            if event_registration_ids:
                db.checkin_logs.delete_many({"registration_id": {"$in": event_registration_ids}})
                db.registration_field_values.delete_many({"registration_id": {"$in": event_registration_ids}})

            if event_field_ids:
                db.registration_field_values.delete_many({"event_field_id": {"$in": event_field_ids}})

            db.event_results.delete_many({"event_id": {"$in": created_event_ids}})
            db.registrations.delete_many({"event_id": {"$in": created_event_ids}})
            db.event_fields.delete_many({"event_id": {"$in": created_event_ids}})
            db.events.delete_many({"id": {"$in": created_event_ids}})

        if user_registration_ids:
            db.checkin_logs.delete_many({"registration_id": {"$in": user_registration_ids}})
            db.registration_field_values.delete_many({"registration_id": {"$in": user_registration_ids}})
            db.event_results.delete_many({"user_id": user_id})
            db.registrations.delete_many({"id": {"$in": user_registration_ids}})

        db.admin_role_requests.delete_many({"$or": [{"user_id": user_id}, {"reviewed_by": user_id}]})
        db.checkin_logs.delete_many({"admin_id": user_id})
        db.event_results.delete_many({"user_id": user_id})
        db.registrations.update_many({"checked_in_by": user_id}, {"$set": {"checked_in_by": None}})
        db.users.delete_one({"id": user_id})

        return user

    @staticmethod
    def review_request(request_id, admin_user_id, approve):
        db = get_db()
        request = db.admin_role_requests.find_one({"id": request_id})
        if not request:
            raise ApiError("Request not found", 404)
        if request.get("status") != "pending":
            raise ApiError("Request already reviewed", 409)

        status = "approved" if approve else "rejected"
        reviewed_at = now_utc()

        db.admin_role_requests.update_one(
            {"id": request_id},
            {"$set": {"status": status, "reviewed_by": admin_user_id, "reviewed_at": reviewed_at, "updated_at": reviewed_at}},
        )

        if approve:
            db.users.update_one({"id": request["user_id"]}, {"$set": {"role": "admin", "updated_at": now_utc()}})

        request["status"] = status
        request["reviewed_by"] = admin_user_id
        request["reviewed_at"] = reviewed_at
        return request
