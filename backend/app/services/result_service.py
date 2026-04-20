from ..extensions import db
from ..models.models import Event, EventResult, Registration


class ResultService:
    @staticmethod
    def upsert_result(event_id, user_id, score, rank, remarks=None):
        result = EventResult.query.filter_by(event_id=event_id, user_id=user_id).first()
        if result:
            result.score = score
            result.rank = rank
            result.remarks = remarks
        else:
            result = EventResult(event_id=event_id, user_id=user_id, score=score, rank=rank, remarks=remarks)
            db.session.add(result)
        db.session.commit()
        return result

    @staticmethod
    def event_results(event_id):
        rows = EventResult.query.filter_by(event_id=event_id).order_by(EventResult.rank.asc()).all()
        registrations = Registration.query.filter_by(event_id=event_id).all()
        return rows, registrations

    @staticmethod
    def attendance_summary(event_id):
        total = Registration.query.filter_by(event_id=event_id).count()
        checked_in = Registration.query.filter_by(event_id=event_id, status="checked_in").count()
        return {
            "total_registered": total,
            "checked_in": checked_in,
            "no_show": max(total - checked_in, 0),
        }
