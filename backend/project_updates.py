"""Read-only update projections from committed, actual business change logs."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from project_changes import NODE_IDS
from project_data import FIELDS, TAIL_FIELDS

try:
    SHANGHAI = ZoneInfo("Asia/Shanghai")
except ZoneInfoNotFoundError:
    # Windows installations without IANA tzdata: modern Shanghai is UTC+08.
    SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")

BUSINESS_FIELDS = tuple(field for field in [*FIELDS, *TAIL_FIELDS, *NODE_IDS]
                        if field not in {"serial", "progressUpdate"})


def update_now():
    return datetime.now(timezone.utc)


def timestamp(value):
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return instant.astimezone(timezone.utc) if instant.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None


def update_index(connection, project_id=None):
    # One query, no business text or employee credentials are loaded/exposed.
    # Initial imports/new project values use initial/create, never these types.
    placeholders = ",".join("?" for _ in BUSINESS_FIELDS)
    sql = f"""SELECT project_id, field_name, changed_at FROM project_change_logs
        WHERE change_type IN ('update','fill','clear','restore')
          AND actor_type IN ('employee','admin_import')
          AND field_name IN ({placeholders}) AND old_value <> new_value"""
    args = list(BUSINESS_FIELDS)
    if project_id is not None:
        sql += " AND project_id=?"
        args.append(project_id)
    result = {}
    for row in connection.execute(sql, args):
        instant = timestamp(row["changed_at"])
        if instant is None:
            continue  # Unknown times cannot be advertised as dated updates.
        fields = result.setdefault(row["project_id"], {})
        field = row["field_name"]
        if field not in fields or instant > fields[field]:
            fields[field] = instant
    return result


def update_metadata(fields, now):
    latest = max(fields.values(), default=None)
    nodes = max((fields[field] for field in NODE_IDS if field in fields), default=None)
    return {
        "updated": bool(latest and latest.astimezone(SHANGHAI).date() == now.astimezone(SHANGHAI).date()),
        "latestBusinessUpdateAt": latest.isoformat() if latest else None,
        "fieldUpdates": {field: fields[field].isoformat() for field in
                         ("situation", "nextStep", "coordination") if field in fields},
        "nodesUpdatedAt": nodes.isoformat() if nodes else None,
    }


def in_update_range(value, now, days):
    instant = timestamp(value)
    if instant is None:
        return False
    today = now.astimezone(SHANGHAI).date()
    return today - timedelta(days=days - 1) <= instant.astimezone(SHANGHAI).date() <= today
