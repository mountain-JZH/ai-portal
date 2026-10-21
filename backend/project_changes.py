"""Immutable project history primitives. Call inside the caller's SQLite transaction."""
from datetime import datetime, timezone
import json
import uuid

TEXT_FIELDS = ("situation", "nextStep", "coordination")
NODE_IDS = tuple(f"stage_{i:02}" for i in range(1, 12))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def migrate(connection):
    columns = {row[1] for row in connection.execute("PRAGMA table_info(projects)")}
    for name, definition in {"version": "INTEGER NOT NULL DEFAULT 1", "created_at": "TEXT",
                             "created_employee_id": "INTEGER", "updated_at": "TEXT",
                             "last_edit_source": "TEXT NOT NULL DEFAULT 'legacy_import'"}.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE projects ADD COLUMN {name} {definition}")
    connection.execute("""CREATE TABLE IF NOT EXISTS project_change_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL,
        change_group_id TEXT NOT NULL, field_name TEXT NOT NULL, old_value TEXT NOT NULL,
        new_value TEXT NOT NULL, employee_id INTEGER, employee_username_snapshot TEXT NOT NULL,
        employee_name_snapshot TEXT NOT NULL, changed_at TEXT, change_type TEXT NOT NULL,
        project_version INTEGER NOT NULL, actor_type TEXT NOT NULL, admin_id INTEGER
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS project_changes_lookup ON project_change_logs(project_id,field_name,id DESC)")
    connection.execute("CREATE INDEX IF NOT EXISTS project_changes_actor ON project_change_logs(employee_id,changed_at)")
    connection.execute("CREATE INDEX IF NOT EXISTS project_changes_time ON project_change_logs(project_id,changed_at,id)")
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS project_initial_baseline ON project_change_logs(project_id,field_name) WHERE change_type='baseline'")
    for row in connection.execute("SELECT * FROM projects WHERE created_at IS NULL").fetchall():
        if connection.execute("SELECT 1 FROM project_change_logs WHERE project_id=? LIMIT 1", (row["id"],)).fetchone():
            continue
        data = json.loads(row["data"])
        group = uuid.uuid4().hex
        for field in TEXT_FIELDS:
            log(connection, row["id"], field, None, data.get(field), None, row["version"], group,
                row["imported_at"] or None, "baseline", "legacy_import")


def log(connection, project_id, field, old, new, employee, version, group, when,
        change_type="update", actor_type="employee", admin_id=None):
    connection.execute("""INSERT INTO project_change_logs
        (project_id,change_group_id,field_name,old_value,new_value,employee_id,
         employee_username_snapshot,employee_name_snapshot,changed_at,change_type,
         project_version,actor_type,admin_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (project_id, group, field, json.dumps(old, ensure_ascii=False), json.dumps(new, ensure_ascii=False),
         employee["id"] if employee else None, employee["username"] if employee else "",
         employee["name"] if employee else "历史台账初始值", when, change_type, version, actor_type, admin_id))


def differences(old, new):
    result = []
    for field in sorted(set(old) | set(new)):
        if field == "stages":
            for index, node in enumerate(NODE_IDS):
                before, after = old.get("stages", [None] * 11)[index], new.get("stages", [None] * 11)[index]
                if before != after:
                    result.append((node, before, after))
        elif old.get(field) != new.get(field):
            result.append((field, old.get(field), new.get(field)))
    return result


def record_changes(connection, project_id, old, new, employee, version, when,
                   actor_type="employee", admin_id=None, creating=False):
    group = uuid.uuid4().hex
    if creating:
        log(connection, project_id, "__created__", None, new.get("name"), employee, version, group, when,
            "create", actor_type, admin_id)
    changed = differences(old, new)
    if creating:
        present = {field for field, _, _ in changed}
        changed.extend((field, None, new.get(field)) for field in TEXT_FIELDS if field not in present)
    for field, before, after in changed:
        kind = "initial" if creating else "clear" if after in (None, "") else "fill" if before in (None, "") else "update"
        if not creating and after not in (None, "") and connection.execute(
            "SELECT 1 FROM project_change_logs WHERE project_id=? AND field_name=? AND (new_value=? OR old_value=?) LIMIT 1",
            (project_id, field, json.dumps(after, ensure_ascii=False), json.dumps(after, ensure_ascii=False))).fetchone():
            kind = "restore"
        log(connection, project_id, field, before, after, employee, version, group, when, kind, actor_type, admin_id)


def metadata(row):
    return {"id": row["id"], "importedAt": row["imported_at"], "importId": row["import_id"],
            "version": row["version"], "createdAt": row["created_at"], "updatedAt": row["updated_at"],
            "lastEditSource": row["last_edit_source"]}
