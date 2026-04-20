from datetime import datetime, timezone

from ..extensions import db


def now_utc():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=now_utc, nullable=False)
    updated_at = db.Column(db.DateTime, default=now_utc, onupdate=now_utc, nullable=False)


class User(db.Model, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")


class AdminRoleRequest(db.Model, TimestampMixin):
    __tablename__ = "admin_role_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)


class Event(db.Model, TimestampMixin):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    registration_deadline = db.Column(db.DateTime, nullable=True)
    max_capacity = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class EventField(db.Model, TimestampMixin):
    __tablename__ = "event_fields"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = db.Column(db.String(120), nullable=False)
    label = db.Column(db.String(255), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)
    is_required = db.Column(db.Boolean, default=True, nullable=False)
    options_json = db.Column(db.Text, nullable=True)
    regex_pattern = db.Column(db.String(255), nullable=True)
    max_length = db.Column(db.Integer, nullable=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)


class Registration(db.Model, TimestampMixin):
    __tablename__ = "registrations"
    __table_args__ = (db.UniqueConstraint("user_id", "event_id", name="uq_user_event"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="registered")
    qr_token = db.Column(db.String(512), nullable=True, unique=True)
    checked_in_at = db.Column(db.DateTime, nullable=True)
    checked_in_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class RegistrationFieldValue(db.Model, TimestampMixin):
    __tablename__ = "registration_field_values"
    __table_args__ = (db.UniqueConstraint("registration_id", "event_field_id", name="uq_registration_field"),)

    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey("registrations.id", ondelete="CASCADE"), nullable=False)
    event_field_id = db.Column(db.Integer, db.ForeignKey("event_fields.id", ondelete="CASCADE"), nullable=False)
    value = db.Column(db.Text, nullable=True)


class CheckinLog(db.Model):
    __tablename__ = "checkin_logs"

    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey("registrations.id", ondelete="CASCADE"), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    result = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    scanned_at = db.Column(db.DateTime, default=now_utc, nullable=False)


class EventResult(db.Model, TimestampMixin):
    __tablename__ = "event_results"
    __table_args__ = (db.UniqueConstraint("event_id", "user_id", name="uq_event_user_result"),)

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(255), nullable=True)
