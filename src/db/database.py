"""
Couche SQLite pour la persistance des dossiers d'expertise.
Les données métier de chaque dossier sont stockées en JSON dans la colonne `data`.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parents[2] / "data" / "ivf.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dossiers (
                id         TEXT PRIMARY KEY,
                reference  TEXT NOT NULL,
                statut     TEXT NOT NULL DEFAULT 'À traiter',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                data       TEXT NOT NULL DEFAULT '{}'
            )
        """)
        conn.commit()


# ── helpers ──────────────────────────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["data"] = json.loads(d["data"])
    return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── CRUD ─────────────────────────────────────────────────────────────────────

def list_dossiers() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, reference, statut, created_at, updated_at FROM dossiers ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def create_dossier() -> dict:
    dossier_id = str(uuid.uuid4())
    year = date.today().year
    short = dossier_id.replace("-", "")[:8].upper()
    reference = f"{year}-UF-{short}"
    now = _now()

    with _connect() as conn:
        conn.execute(
            "INSERT INTO dossiers (id, reference, statut, created_at, updated_at, data) VALUES (?,?,?,?,?,?)",
            (dossier_id, reference, "À traiter", now, now, "{}"),
        )
        conn.commit()

    return get_dossier(dossier_id)  # type: ignore[return-value]


def get_dossier(dossier_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM dossiers WHERE id = ?", (dossier_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def update_dossier(dossier_id: str, payload: dict[str, Any]) -> dict | None:
    current = get_dossier(dossier_id)
    if current is None:
        return None

    statut = payload.get("statut", current["statut"])
    # Deep-merge nested data
    data = current["data"]
    if "data" in payload and isinstance(payload["data"], dict):
        data = _deep_merge(data, payload["data"])

    with _connect() as conn:
        conn.execute(
            "UPDATE dossiers SET statut=?, updated_at=?, data=? WHERE id=?",
            (statut, _now(), json.dumps(data, ensure_ascii=False), dossier_id),
        )
        conn.commit()

    return get_dossier(dossier_id)


def delete_dossier(dossier_id: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM dossiers WHERE id = ?", (dossier_id,))
        conn.commit()


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result
