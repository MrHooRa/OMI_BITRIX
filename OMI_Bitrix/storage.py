from contextlib import contextmanager
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path


class ConfigStore:
    """SQLite is intentionally configuration-only.

    Each browser receives an anonymous profile id. This is not authentication;
    it simply keeps each employee's webhook, selected projects and preferences
    separate when several people use the same Flask instance.
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        self._init_db()

    @contextmanager
    def _connect(self):
        con = sqlite3.connect(self.db_path, timeout=10)
        con.row_factory = sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            # Legacy tables are kept so upgrades from the earlier single-user
            # build can be migrated into the first browser profile.
            con.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            con.execute(
                "CREATE TABLE IF NOT EXISTS selected_projects ("
                "project_id TEXT PRIMARY KEY, project_name TEXT NOT NULL)"
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    profile_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS profile_settings (
                    profile_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY(profile_id, key)
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS profile_projects (
                    profile_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    PRIMARY KEY(profile_id, project_id)
                )
                """
            )

    @staticmethod
    def _decode(value, default=None):
        if value is None:
            return default
        try:
            return json.loads(value)
        except Exception:
            return value

    def ensure_profile(self, profile_id):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._lock, self._connect() as con:
            existed = con.execute(
                "SELECT 1 FROM profiles WHERE profile_id=?", (profile_id,)
            ).fetchone()
            if existed:
                con.execute("UPDATE profiles SET last_seen=? WHERE profile_id=?", (now, profile_id))
                return

            con.execute(
                "INSERT INTO profiles(profile_id, created_at, last_seen) VALUES(?,?,?)",
                (profile_id, now, now),
            )

            # Migrate the earlier single-user configuration into the very first
            # profile only. Subsequent browsers start with a clean setup.
            count = con.execute("SELECT COUNT(*) AS n FROM profile_settings").fetchone()["n"]
            if count == 0:
                legacy = con.execute("SELECT key, value FROM settings").fetchall()
                if legacy:
                    con.executemany(
                        "INSERT OR REPLACE INTO profile_settings(profile_id,key,value) VALUES(?,?,?)",
                        [(profile_id, r["key"], r["value"]) for r in legacy],
                    )
                    projects = con.execute(
                        "SELECT project_id, project_name FROM selected_projects"
                    ).fetchall()
                    con.executemany(
                        "INSERT OR REPLACE INTO profile_projects(profile_id,project_id,project_name) VALUES(?,?,?)",
                        [(profile_id, r["project_id"], r["project_name"]) for r in projects],
                    )

    def get(self, key, default=None, profile_id=None):
        if profile_id is None:
            # Legacy compatibility for scripts/tests. New app code always passes profile_id.
            with self._connect() as con:
                row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return self._decode(row["value"] if row else None, default)
        with self._connect() as con:
            row = con.execute(
                "SELECT value FROM profile_settings WHERE profile_id=? AND key=?",
                (profile_id, key),
            ).fetchone()
        return self._decode(row["value"] if row else None, default)

    def set(self, key, value, profile_id=None):
        payload = json.dumps(value, ensure_ascii=False)
        with self._lock, self._connect() as con:
            if profile_id is None:
                con.execute(
                    "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, payload),
                )
            else:
                self._upsert_setting(con, profile_id, key, payload)

    def set_many(self, values, profile_id=None):
        with self._lock, self._connect() as con:
            for key, value in values.items():
                payload = json.dumps(value, ensure_ascii=False)
                if profile_id is None:
                    con.execute(
                        "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (key, payload),
                    )
                else:
                    self._upsert_setting(con, profile_id, key, payload)

    @staticmethod
    def _upsert_setting(con, profile_id, key, payload):
        con.execute(
            """
            INSERT INTO profile_settings(profile_id,key,value) VALUES(?,?,?)
            ON CONFLICT(profile_id,key) DO UPDATE SET value=excluded.value
            """,
            (profile_id, key, payload),
        )

    def workspace_root(self, profile_id=None):
        return (
            self.get("vault_root", profile_id=profile_id)
            or self.get("obsidian_vault", profile_id=profile_id)
            or self.get("shared_root", profile_id=profile_id)
        )

    def configured(self, profile_id=None):
        return bool(
            self.get("webhook_url", profile_id=profile_id)
            and self.workspace_root(profile_id)
            and self.get("employee_name", profile_id=profile_id)
        )

    def projects(self, profile_id=None):
        if profile_id is None:
            with self._connect() as con:
                rows = con.execute(
                    "SELECT project_id, project_name FROM selected_projects ORDER BY project_name"
                ).fetchall()
        else:
            with self._connect() as con:
                rows = con.execute(
                    "SELECT project_id, project_name FROM profile_projects WHERE profile_id=? ORDER BY project_name",
                    (profile_id,),
                ).fetchall()
        return [{"id": r["project_id"], "name": r["project_name"]} for r in rows]

    def replace_projects(self, projects, profile_id=None):
        with self._lock, self._connect() as con:
            if profile_id is None:
                con.execute("DELETE FROM selected_projects")
                con.executemany(
                    "INSERT INTO selected_projects(project_id, project_name) VALUES(?, ?)",
                    [(str(p["id"]), p["name"]) for p in projects],
                )
            else:
                con.execute("DELETE FROM profile_projects WHERE profile_id=?", (profile_id,))
                con.executemany(
                    "INSERT INTO profile_projects(profile_id,project_id,project_name) VALUES(?,?,?)",
                    [(profile_id, str(p["id"]), p["name"]) for p in projects],
                )

    def profile_ids(self):
        with self._connect() as con:
            return [r["profile_id"] for r in con.execute("SELECT profile_id FROM profiles")]

    def configured_profiles(self):
        with self._connect() as con:
            rows = con.execute("SELECT profile_id FROM profiles ORDER BY last_seen DESC").fetchall()
        return [r["profile_id"] for r in rows if self.configured(r["profile_id"])]
