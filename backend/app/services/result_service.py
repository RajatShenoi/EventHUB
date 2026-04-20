from ..core.errors import ApiError
from ..extensions import db
from ..models.models import Event, EventField, EventResult, Registration, RegistrationFieldValue, User


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

    @staticmethod
    def event_participants_with_fields(event_id):
        fields = EventField.query.filter_by(event_id=event_id).order_by(EventField.display_order.asc()).all()
        registrations = (
            Registration.query.filter_by(event_id=event_id, status="checked_in")
            .order_by(Registration.created_at.asc())
            .all()
        )
        existing_results = {item.user_id: item for item in EventResult.query.filter_by(event_id=event_id).all()}

        rows = []
        for registration in registrations:
            user = User.query.get(registration.user_id)
            if not user:
                continue

            values = RegistrationFieldValue.query.filter_by(registration_id=registration.id).all()
            values_map = {}
            for value in values:
                field = EventField.query.get(value.event_field_id)
                if field:
                    values_map[field.field_name] = value.value

            existing = existing_results.get(user.id)
            rows.append(
                {
                    "registration_id": registration.id,
                    "user_id": user.id,
                    "full_name": user.full_name,
                    "field_values": values_map,
                    "score": existing.score if existing else None,
                    "rank": existing.rank if existing else None,
                    "remarks": existing.remarks if existing else "",
                }
            )

        return {
            "fields": [{"field_name": field.field_name, "label": field.label} for field in fields],
            "participants": rows,
        }

    @staticmethod
    def publish_scores(event_id, score_entries):
        registrations = Registration.query.filter_by(event_id=event_id, status="checked_in").all()
        valid_user_ids = {item.user_id for item in registrations}

        parsed_entries = []
        for entry in score_entries:
            user_id = entry.get("user_id")
            if user_id not in valid_user_ids:
                continue

            score = entry.get("score")
            if score is None or str(score).strip() == "":
                continue

            parsed_entries.append(
                {
                    "user_id": user_id,
                    "score": float(score),
                    "remarks": entry.get("remarks", ""),
                }
            )

        requested_user_ids = {
            entry.get("user_id")
            for entry in score_entries
            if entry.get("user_id") is not None and entry.get("score") not in [None, ""]
        }
        invalid_user_ids = sorted(user_id for user_id in requested_user_ids if user_id not in valid_user_ids)
        if invalid_user_ids:
            invalid_list = ", ".join(str(item) for item in invalid_user_ids)
            raise ApiError(f"Scores can be published only for checked-in users. Invalid user IDs: {invalid_list}", 422)

        sorted_entries = sorted(parsed_entries, key=lambda item: (-item["score"], item["user_id"]))

        current_rank = 0
        last_score = None
        for index, item in enumerate(sorted_entries, start=1):
            if last_score is None or item["score"] != last_score:
                current_rank = index
                last_score = item["score"]
            item["rank"] = current_rank

            result = EventResult.query.filter_by(event_id=event_id, user_id=item["user_id"]).first()
            if result:
                result.score = item["score"]
                result.rank = item["rank"]
                result.remarks = item["remarks"]
            else:
                db.session.add(
                    EventResult(
                        event_id=event_id,
                        user_id=item["user_id"],
                        score=item["score"],
                        rank=item["rank"],
                        remarks=item["remarks"],
                    )
                )

        db.session.commit()

        return [
            {
                "user_id": item["user_id"],
                "score": item["score"],
                "rank": item["rank"],
                "remarks": item["remarks"],
            }
            for item in sorted_entries
        ]
