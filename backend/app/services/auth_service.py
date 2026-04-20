from flask_jwt_extended import create_access_token

from ..core.errors import ApiError
from ..core.security import hash_password, verify_password
from ..extensions import db
from ..models.models import AdminRoleRequest, CheckinLog, Event, EventField, EventResult, Registration, RegistrationFieldValue, User


class AuthService:
    @staticmethod
    def register_user(email, full_name, password):
        existing = User.query.filter_by(email=email).first()
        if existing:
            raise ApiError("Email already exists", 409)

        user = User(email=email, full_name=full_name, password_hash=hash_password(password), role="user")
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def login(email, password):
        user = User.query.filter_by(email=email).first()
        if not user or not verify_password(password, user.password_hash):
            raise ApiError("Invalid credentials", 401)

        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return user, token

    @staticmethod
    def request_admin_role(user_id, reason):
        existing_pending = AdminRoleRequest.query.filter_by(user_id=user_id, status="pending").first()
        if existing_pending:
            raise ApiError("You already have a pending request", 409)

        request = AdminRoleRequest(user_id=user_id, reason=reason, status="pending")
        db.session.add(request)
        db.session.commit()
        return request

    @staticmethod
    def list_pending_requests():
        return AdminRoleRequest.query.filter_by(status="pending").order_by(AdminRoleRequest.created_at.desc()).all()

    @staticmethod
    def list_all_requests():
        return AdminRoleRequest.query.order_by(AdminRoleRequest.created_at.desc()).all()

    @staticmethod
    def list_users():
        return User.query.order_by(User.created_at.desc()).all()

    @staticmethod
    def get_user(user_id):
        user = User.query.get(user_id)
        if not user:
            raise ApiError("User not found", 404)
        return user

    @staticmethod
    def update_user(user_id, payload):
        user = AuthService.get_user(user_id)

        email = payload.get("email")
        full_name = payload.get("full_name")
        role = payload.get("role")

        if email and email.lower() != user.email:
            existing = User.query.filter_by(email=email.lower()).first()
            if existing:
                raise ApiError("Email already exists", 409)
            user.email = email.lower()

        if full_name:
            user.full_name = full_name

        if role in {"user", "admin"}:
            user.role = role

        db.session.commit()
        return user

    @staticmethod
    def delete_user(user_id):
        user = AuthService.get_user(user_id)

        created_event_ids = [event.id for event in Event.query.filter_by(created_by=user_id).all()]
        user_registration_ids = [item.id for item in Registration.query.filter_by(user_id=user_id).all()]

        if created_event_ids:
            event_registration_ids = [
                item.id
                for item in Registration.query.filter(Registration.event_id.in_(created_event_ids)).all()
            ]
            event_field_ids = [
                item.id for item in EventField.query.filter(EventField.event_id.in_(created_event_ids)).all()
            ]

            if event_registration_ids:
                CheckinLog.query.filter(CheckinLog.registration_id.in_(event_registration_ids)).delete(synchronize_session=False)
                RegistrationFieldValue.query.filter(RegistrationFieldValue.registration_id.in_(event_registration_ids)).delete(
                    synchronize_session=False
                )

            EventResult.query.filter(EventResult.event_id.in_(created_event_ids)).delete(synchronize_session=False)
            Registration.query.filter(Registration.event_id.in_(created_event_ids)).delete(synchronize_session=False)
            EventField.query.filter(EventField.event_id.in_(created_event_ids)).delete(synchronize_session=False)
            Event.query.filter(Event.id.in_(created_event_ids)).delete(synchronize_session=False)

        if user_registration_ids:
            CheckinLog.query.filter(CheckinLog.registration_id.in_(user_registration_ids)).delete(synchronize_session=False)
            RegistrationFieldValue.query.filter(RegistrationFieldValue.registration_id.in_(user_registration_ids)).delete(
                synchronize_session=False
            )
            EventResult.query.filter(EventResult.user_id == user_id).delete(synchronize_session=False)
            Registration.query.filter(Registration.id.in_(user_registration_ids)).delete(synchronize_session=False)

        AdminRoleRequest.query.filter(
            (AdminRoleRequest.user_id == user_id) | (AdminRoleRequest.reviewed_by == user_id)
        ).delete(synchronize_session=False)

        CheckinLog.query.filter(CheckinLog.admin_id == user_id).delete(synchronize_session=False)
        EventResult.query.filter(EventResult.user_id == user_id).delete(synchronize_session=False)
        Registration.query.filter(Registration.checked_in_by == user_id).update(
            {Registration.checked_in_by: None}, synchronize_session=False
        )

        db.session.delete(user)
        db.session.commit()
        return user

    @staticmethod
    def review_request(request_id, admin_user_id, approve):
        request = AdminRoleRequest.query.get(request_id)
        if not request:
            raise ApiError("Request not found", 404)

        if request.status != "pending":
            raise ApiError("Request already reviewed", 409)

        request.status = "approved" if approve else "rejected"
        request.reviewed_by = admin_user_id
        from ..models.models import now_utc

        request.reviewed_at = now_utc()

        if approve:
            user = User.query.get(request.user_id)
            if user:
                user.role = "admin"

        db.session.commit()
        return request
