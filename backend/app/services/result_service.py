import json

from ..core.errors import ApiError
from ..db.mongo import get_db, next_id, now_utc


class ResultService:
    @staticmethod
    def upsert_result(event_id, user_id, score, rank, remarks=None):
        db = get_db()
        existing = db.event_results.find_one({"event_id": event_id, "user_id": user_id})
        now = now_utc()

        if existing:
            db.event_results.update_one(
                {"id": existing["id"]},
                {"$set": {"score": score, "rank": rank, "remarks": remarks, "updated_at": now}},
            )
            existing["score"] = score
            existing["rank"] = rank
            existing["remarks"] = remarks
            existing["updated_at"] = now
            return existing

        result = {
            "id": next_id("event_results"),
            "event_id": event_id,
            "user_id": user_id,
            "score": score,
            "rank": rank,
            "remarks": remarks,
            "created_at": now,
            "updated_at": now,
        }
        db.event_results.insert_one(result)
        return result

    @staticmethod
    def event_results(event_id):
        db = get_db()
        rows = list(db.event_results.find({"event_id": event_id}).sort("rank", 1))
        registrations = list(db.registrations.find({"event_id": event_id}))
        return rows, registrations

    @staticmethod
    def attendance_summary(event_id):
        db = get_db()
        total = db.registrations.count_documents({"event_id": event_id})
        checked_in = db.registrations.count_documents({"event_id": event_id, "status": "checked_in"})
        return {
            "total_registered": total,
            "checked_in": checked_in,
            "no_show": max(total - checked_in, 0),
        }

    @staticmethod
    def all_event_registrations_with_fields(event_id):
        db = get_db()
        fields = list(db.event_fields.find({"event_id": event_id}).sort("display_order", 1))
        registrations = list(db.registrations.find({"event_id": event_id}).sort("created_at", 1))

        rows = []
        for registration in registrations:
            user = db.users.find_one({"id": registration["user_id"]})
            if not user:
                continue

            values = list(db.registration_field_values.find({"registration_id": registration["id"]}))
            field_ids = [item["event_field_id"] for item in values]
            field_docs = list(db.event_fields.find({"id": {"$in": field_ids}})) if field_ids else []
            field_map_by_id = {item["id"]: item for item in field_docs}

            values_map = {}
            for value in values:
                field = field_map_by_id.get(value["event_field_id"])
                if field:
                    values_map[field["field_name"]] = value.get("value")

            rows.append(
                {
                    "registration_id": registration["id"],
                    "user_id": user["id"],
                    "full_name": user["full_name"],
                    "check_in_status": registration.get("status"),
                    "field_values": values_map,
                }
            )

        return {
            "fields": [
                {
                    "field_name": field["field_name"],
                    "label": field["label"],
                    "field_type": field["field_type"],
                    "is_required": field.get("is_required", True),
                    "options": json.loads(field.get("options_json") or "[]") if field.get("field_type") in ["select", "radio"] else [],
                }
                for field in fields
            ],
            "registrations": rows,
        }

    @staticmethod
    def event_participants_with_fields(event_id):
        db = get_db()
        fields = list(db.event_fields.find({"event_id": event_id}).sort("display_order", 1))
        registrations = list(db.registrations.find({"event_id": event_id, "status": "checked_in"}).sort("created_at", 1))
        existing_results = {
            item["user_id"]: item for item in db.event_results.find({"event_id": event_id})
        }

        rows = []
        for registration in registrations:
            user = db.users.find_one({"id": registration["user_id"]})
            if not user:
                continue

            values = list(db.registration_field_values.find({"registration_id": registration["id"]}))
            field_ids = [item["event_field_id"] for item in values]
            field_docs = list(db.event_fields.find({"id": {"$in": field_ids}})) if field_ids else []
            field_map_by_id = {item["id"]: item for item in field_docs}

            values_map = {}
            for value in values:
                field = field_map_by_id.get(value["event_field_id"])
                if field:
                    values_map[field["field_name"]] = value.get("value")

            existing = existing_results.get(user["id"])
            rows.append(
                {
                    "registration_id": registration["id"],
                    "user_id": user["id"],
                    "full_name": user["full_name"],
                    "field_values": values_map,
                    "score": existing.get("score") if existing else None,
                    "rank": existing.get("rank") if existing else None,
                    "remarks": existing.get("remarks") if existing else "",
                }
            )

        return {
            "fields": [{"field_name": field["field_name"], "label": field["label"]} for field in fields],
            "participants": rows,
        }

    @staticmethod
    def publish_scores(event_id, score_entries):
        db = get_db()
        registrations = list(db.registrations.find({"event_id": event_id, "status": "checked_in"}))
        valid_user_ids = {item["user_id"] for item in registrations}

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
        now = now_utc()
        for index, item in enumerate(sorted_entries, start=1):
            if last_score is None or item["score"] != last_score:
                current_rank = index
                last_score = item["score"]
            item["rank"] = current_rank

            existing = db.event_results.find_one({"event_id": event_id, "user_id": item["user_id"]})
            if existing:
                db.event_results.update_one(
                    {"id": existing["id"]},
                    {"$set": {"score": item["score"], "rank": item["rank"], "remarks": item["remarks"], "updated_at": now}},
                )
            else:
                db.event_results.insert_one(
                    {
                        "id": next_id("event_results"),
                        "event_id": event_id,
                        "user_id": item["user_id"],
                        "score": item["score"],
                        "rank": item["rank"],
                        "remarks": item["remarks"],
                        "created_at": now,
                        "updated_at": now,
                    }
                )

        return [
            {
                "user_id": item["user_id"],
                "score": item["score"],
                "rank": item["rank"],
                "remarks": item["remarks"],
            }
            for item in sorted_entries
        ]
