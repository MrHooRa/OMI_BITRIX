"""Local, connection-scoped task snapshots. Configuration and credentials stay separate."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path


class HistoryDatabase:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection, connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS history_sources (
                    profile TEXT NOT NULL, source TEXT NOT NULL, scope TEXT NOT NULL,
                    metadata TEXT NOT NULL, PRIMARY KEY(profile, source));
                CREATE TABLE IF NOT EXISTS history_records (
                    profile TEXT NOT NULL, source TEXT NOT NULL, ordinal INTEGER NOT NULL,
                    task_source TEXT NOT NULL, task_id TEXT NOT NULL,
                    search_text TEXT NOT NULL, payload TEXT NOT NULL,
                    PRIMARY KEY(profile, source, task_source, task_id));
                CREATE INDEX IF NOT EXISTS history_order ON history_records(profile, source, ordinal);
            """)

    def connect(self):
        return sqlite3.connect(self.path, timeout=30)

    def load(self, profile, source, scope):
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT scope, metadata FROM history_sources WHERE profile=? AND source=?",
                                     (profile, source)).fetchone()
            if not row or row[0] != scope:
                return None
            result = json.loads(row[1])
            result["records"] = [json.loads(row[0]) for row in connection.execute(
                "SELECT payload FROM history_records WHERE profile=? AND source=? ORDER BY ordinal", (profile, source))]
            return result

    def save(self, profile, source, scope, snapshot):
        metadata = {key: value for key, value in snapshot.items() if key != "records"}
        with closing(self.connect()) as connection, connection:
            old = connection.execute("SELECT scope, metadata FROM history_sources WHERE profile=? AND source=?",
                                     (profile, source)).fetchone()
            previous = json.loads(old[1]) if old and old[0] == scope else {}
            if previous.get("digest") != snapshot["digest"]:
                connection.execute("DELETE FROM history_records WHERE profile=? AND source=?", (profile, source))
                connection.executemany("INSERT INTO history_records VALUES (?,?,?,?,?,?,?)", (
                    (profile, source, position, record.get("source", source), str(record["id"]),
                     " ".join(str(record.get(key) or "") for key in
                              ("id", "title", "request_id", "category", "assignee_name", "status_label")).casefold(),
                     json.dumps(record, ensure_ascii=False))
                    for position, record in enumerate(snapshot["records"])))
            connection.execute("INSERT OR REPLACE INTO history_sources VALUES (?,?,?,?)",
                               (profile, source, scope, json.dumps(metadata, ensure_ascii=False)))

    def delete(self, profile, source):
        with closing(self.connect()) as connection, connection:
            connection.execute("DELETE FROM history_records WHERE profile=? AND source=?", (profile, source))
            connection.execute("DELETE FROM history_sources WHERE profile=? AND source=?", (profile, source))

    def page(self, profile, source, scope, page=1, query="", task_source=""):
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT metadata FROM history_sources WHERE profile=? AND source=? AND scope=?",
                                     (profile, source, scope)).fetchone()
            if not row:
                return None
            conditions, params = ["profile=?", "source=?"], [profile, source]
            if query:
                conditions.append("instr(search_text, ?)>0")
                params.append(query.casefold())
            if task_source:
                conditions.append("task_source=?")
                params.append(task_source)
            where = " AND ".join(conditions)
            count = connection.execute("SELECT COUNT(*) FROM history_records WHERE " + where, params).fetchone()[0]
            records = [json.loads(row[0]) for row in connection.execute(
                "SELECT payload FROM history_records WHERE " + where + " ORDER BY ordinal LIMIT 50 OFFSET ?",
                [*params, (max(1, page) - 1) * 50])]
            return records, count
