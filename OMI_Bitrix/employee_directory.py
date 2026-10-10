"""Profile/connection-scoped identity links; names never establish identity.

Only configuration is persisted. Observations remain in memory and use the
profile's existing source permissions. Linking never grants assignment rights.
"""
import hashlib
import json
import uuid
from datetime import date, datetime
from history import connection_scope
from recommendation_matching import RelevanceIndex
from sla import parse, TZ
from recommendations import assignment_state


class EmployeeDirectory:
    def __init__(self, store, history, services):
        self.store, self.history, self.services = store, history, services
        for service in services.values():
            service.unified_directory = self

    def observations(self, pid):
        accounts, snapshots = {}, {}
        for source, service in self.services.items():
            context = service.context(pid)
            if not context:
                continue
            cache = "diwan_analysis" if source == "diwan" else "bitrix"
            self.history.bind_scope(pid, cache, connection_scope(self.store, pid, source))
            snapshot = self.history.source(pid, cache, copy_records=False)
            state = service._state(context)
            # Never acquire another service lock while a caller holds its own.
            # Active arrays are published atomically; source snapshots are copies.
            active = list(state["active"])
            people = service.source_directory(context, state)
            scope = hashlib.sha256(context["shared_key"].encode()).hexdigest()
            known = {str(p["id"]): dict(p) for p in people}
            for row in snapshot["records"] + active:
                ident = str(row.get("assignee_id") or "")
                if ident and ident != "0":
                    known.setdefault(ident, {"id": ident, "name": row.get("assignee_name") or ident,
                        "enabled": False, "active": True, "projects": ["diwan"] if source == "diwan" else [],
                        "categories": [], "basis": "history_unconfirmed"})
                    for key in ("email", "department", "position"):
                        if row.get("assignee_" + key) and not known[ident].get(key):
                            known[ident][key] = row["assignee_" + key]
            for ident, person in known.items():
                accounts[(source, ident)] = {**person, "source": source, "scope": scope}
            snapshots[source] = {**snapshot, "active": active, "scope": scope,
                "checked_epoch": state.get("checked_epoch", 0), "open_error": state.get("error") or state.get("directory_error"),
                "open_checked": state.get("checked_at")}
        return accounts, snapshots

    def snapshot(self, pid):
        accounts, sources = self.observations(pid)
        configured = self.store.get("employee_directory", [], profile_id=pid)
        used, people = set(), []
        for entry in configured:
            aliases = [{**accounts[(a["source"], a["id"])],
                        "source_enabled": accounts[(a["source"], a["id"])].get("enabled", False),
                        "enabled": accounts[(a["source"], a["id"])].get("enabled", False)
                        if "enabled" not in a else (a["enabled"] and (a["source"] == "diwan" or accounts[(a["source"], a["id"])].get("enabled", False)))} for a in entry["accounts"]
                       if (a["source"], a["id"]) in accounts
                       and accounts[(a["source"], a["id"])]["scope"] == a["scope"]]
            if not aliases:
                continue
            used.update((a["source"], a["id"]) for a in aliases)
            people.append({**entry, "accounts": aliases, "linked": len(aliases) > 1})
        for key, account in accounts.items():
            if key not in used:
                person_id = hashlib.sha256(json.dumps([pid, account["scope"], *key]).encode()).hexdigest()[:24]
                people.append({"person_id": person_id, "name": account["name"], "team": "",
                    "active": True, "away_from": "", "away_to": "", "accounts": [account], "linked": False})
        return {"people": sorted(people, key=lambda p: (p["name"], p["person_id"])),
                "sources": {s: {"count": len(v["records"]), "complete": v["complete"],
                    "updated_at": v["updated_at"], "error": v["error"]} for s, v in sources.items()}}

    def save(self, pid, entries):
        if not isinstance(entries, list) or len(entries) > 1000:
            raise ValueError("Invalid employee directory")
        accounts, _ = self.observations(pid)
        previous_entries = {p["person_id"]: p for p in self.store.get("employee_directory", [], profile_id=pid)}
        used, ids, clean = set(), set(), []
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("accounts"), list):
                raise ValueError("Invalid employee accounts")
            aliases = entry["accounts"]
            if not 1 <= len(aliases) <= 2:
                raise ValueError("Choose one account per source")
            values, seen_sources = [], set()
            for alias in aliases:
                if not isinstance(alias, dict):
                    raise ValueError("Invalid employee account")
                key = (str(alias.get("source", "")), str(alias.get("id", "")))
                account = accounts.get(key)
                if not account or key in used or key[0] in seen_sources:
                    raise ValueError("Unknown, duplicate or already linked account")
                if alias.get("scope") != account["scope"]:
                    raise ValueError("Connection changed; reload the employee directory")
                used.add(key); seen_sources.add(key[0])
                values.append({"source": key[0], "id": key[1], "scope": account["scope"],
                    "enabled": alias.get("enabled", account.get("enabled", False)) is True})
            ident = str(entry.get("person_id") or uuid.uuid4().hex)
            if len(ident) > 64 or ident in ids:
                raise ValueError("Invalid person identifier")
            ids.add(ident)
            chosen_sources = {a["source"] for a in values}
            for old in previous_entries.get(ident, {}).get("accounts", []):
                account = accounts.get((old["source"], old["id"]))
                if old["source"] not in chosen_sources and (not account or account["scope"] != old["scope"]):
                    values.append(old)
            row = {"person_id": ident, "accounts": values, "active": entry.get("active") is not False,
                **{key: str(entry.get(key) or "").strip()[:200] for key in ("name", "team", "away_from", "away_to")}}
            row["name"] = row["name"] or accounts[(values[0]["source"], values[0]["id"])]["name"]
            if bool(row["away_from"]) != bool(row["away_to"]):
                raise ValueError("Specify both absence dates")
            if row["away_from"] and date.fromisoformat(row["away_from"]) > date.fromisoformat(row["away_to"]):
                raise ValueError("Invalid absence interval")
            clean.append(row)
        # Preserve links for entirely disconnected sources; an unrelated save
        # must not silently erase them. Their scopes still gate future use.
        present = set(ids)
        for previous in self.store.get("employee_directory", [], profile_id=pid):
            if previous["person_id"] not in present and not any(
                (a["source"], a["id"]) in accounts and accounts[(a["source"], a["id"])]["scope"] == a["scope"]
                for a in previous["accounts"]):
                clean.append(previous)
        self.store.set("employee_directory", clean, profile_id=pid)
        return self.snapshot(pid)

    def source_people(self, pid, source):
        result = []
        for person in self.snapshot(pid)["people"]:
            account = next((a for a in person["accounts"] if a["source"] == source), None)
            if account:
                result.append({**account, "name": person["name"], "person_id": person["person_id"],
                    "team": person["team"], "linked_sources": [a["source"] for a in person["accounts"]],
                    "active": account.get("active", True) and person["active"],
                    "away_from": person["away_from"] or account.get("away_from", ""),
                    "away_to": person["away_to"] or account.get("away_to", "")})
        return result

    def inputs(self, pid, source, native_index, native_active, state):
        _, sources = self.observations(pid)
        people = self.snapshot(pid)["people"]
        rows, active = list(native_index.records), list(native_active)
        instant, statuses, mapping = datetime.now(TZ), [], {}
        for person in people:
            target = next((a for a in person["accounts"] if a["source"] == source), None)
            if target:
                for alias in person["accounts"]:
                    if (alias["source"] != source and alias["scope"] == sources.get(alias["source"], {}).get("scope")
                            and target["scope"] == sources.get(source, {}).get("scope")):
                        mapping[(alias["source"], alias["id"])] = (target["id"], person["person_id"])
        for peer, snapshot in sources.items():
            if peer == source:
                continue
            peer_context = self.services[peer].context(pid)
            if not peer_context or hashlib.sha256(peer_context["shared_key"].encode()).hexdigest() != snapshot["scope"]:
                continue
            selected = []
            for row in snapshot["records"]:
                link = mapping.get((peer, row.get("assignee_id")))
                created, closed = parse(row.get("created_at")), parse(row.get("completed_at"))
                if link and row.get("completed") and created and closed and created < closed < instant:
                    selected.append({**row, "source_assignee_id": row["assignee_id"],
                        "assignee_id": link[0], "person_id": link[1]})
            rows.extend(selected)
            relevant_open = [r for r in snapshot["active"] if (peer, r.get("assignee_id")) in mapping]
            journal = self.services[peer].journal.read(peer_context["shared_key"])
            for row in relevant_open:
                row = {**row, "awaiting_executor": assignment_state(row, {},
                    journal["tasks"].get(row["id"])) == "needs_assignment"}
                link = mapping[(peer, row["assignee_id"])]
                active.append({**row, "source_assignee_id": row["assignee_id"], "assignee_id": link[0], "person_id": link[1]})
            if selected or relevant_open:
                statuses.append({"source": peer, "complete": snapshot["complete"] and not snapshot["error"],
                    "updated_at": snapshot["updated_at"], "open_fresh": bool(snapshot["open_checked"])
                    and not snapshot["open_error"] and self.services[peer].clock() - snapshot["checked_epoch"] <= 120})
        signature = hashlib.sha256(json.dumps([rows, native_index.domain_rules], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if state.get("federated_revision") != signature:
            state["federated_index"] = RelevanceIndex(rows, domain_rules=native_index.domain_rules) if len(rows) != len(native_index.records) else native_index
            state["federated_revision"] = signature
        return state["federated_index"], active, statuses

