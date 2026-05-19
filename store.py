"""SQLite persistence layer for clinical trial data."""
import sqlite3
import json
import pandas as pd
from pathlib import Path
from collections import Counter
from config import DB_PATH


def _conn() -> sqlite3.Connection:
    """Open (or create) the SQLite connection, ensuring the data directory exists."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db() -> None:
    """Create the trials table and indexes if they do not already exist."""
    con = _conn()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS trials (
            nct_id          TEXT PRIMARY KEY,
            title           TEXT,
            status          TEXT,
            phase           TEXT,
            disease_area    TEXT,
            conditions      TEXT,
            sponsor         TEXT,
            countries       TEXT,
            start_date      TEXT,
            completion_date TEXT,
            study_type      TEXT,
            brief_summary   TEXT,
            fetched_at      TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_status       ON trials(status);
        CREATE INDEX IF NOT EXISTS idx_phase        ON trials(phase);
        CREATE INDEX IF NOT EXISTS idx_disease_area ON trials(disease_area);
        CREATE INDEX IF NOT EXISTS idx_sponsor      ON trials(sponsor);
    """)
    con.commit()
    con.close()


def upsert_trials(rows: list[dict]) -> None:
    """Insert or replace trial rows, serialising list fields to JSON."""
    if not rows:
        return
    con = _conn()
    for r in rows:
        try:
            con.execute("""
                INSERT OR REPLACE INTO trials
                    (nct_id, title, status, phase, disease_area,
                     conditions, sponsor, countries, start_date,
                     completion_date, study_type, brief_summary)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                r.get("nct_id"),
                r.get("title"),
                r.get("status"),
                r.get("phase"),
                r.get("disease_area"),
                json.dumps(r.get("conditions") or []),
                r.get("sponsor"),
                json.dumps(r.get("countries") or []),
                r.get("start_date"),
                r.get("completion_date"),
                r.get("study_type"),
                r.get("brief_summary"),
            ))
        except Exception as exc:
            print(f"[store] upsert error for {r.get('nct_id')}: {exc}")
    con.commit()
    con.close()


def get_trials() -> pd.DataFrame:
    """Return all trials as a DataFrame with conditions/countries as Python lists."""
    try:
        con = _conn()
        df  = pd.read_sql("SELECT * FROM trials ORDER BY fetched_at DESC", con)
        con.close()
        if df.empty:
            return df
        df["conditions"] = df["conditions"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else []
        )
        df["countries"] = df["countries"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else []
        )
        return df
    except Exception as exc:
        print(f"[store] get_trials error: {exc}")
        return pd.DataFrame()


def get_stats() -> dict:
    """Return aggregate counts used by the dashboard KPI cards."""
    try:
        con = _conn()
        total_row = con.execute("SELECT COUNT(*) FROM trials").fetchone()
        total     = total_row[0] if total_row else 0

        by_status = dict(con.execute(
            "SELECT status, COUNT(*) FROM trials GROUP BY status"
        ).fetchall())

        by_phase = dict(con.execute(
            "SELECT phase, COUNT(*) FROM trials GROUP BY phase"
        ).fetchall())

        by_disease = dict(con.execute(
            "SELECT disease_area, COUNT(*) FROM trials GROUP BY disease_area"
        ).fetchall())

        # country counts require JSON parsing — do it in Python
        country_rows = con.execute(
            "SELECT countries FROM trials WHERE countries IS NOT NULL"
        ).fetchall()
        con.close()

        country_ctr: Counter = Counter()
        for (raw,) in country_rows:
            try:
                for c in json.loads(raw):
                    country_ctr[c] += 1
            except Exception:
                pass

        return {
            "total":      total,
            "by_status":  by_status,
            "by_phase":   by_phase,
            "by_disease": by_disease,
            "by_country": dict(country_ctr.most_common(50)),
        }
    except Exception as exc:
        print(f"[store] get_stats error: {exc}")
        return {"total": 0, "by_status": {}, "by_phase": {}, "by_disease": {}, "by_country": {}}


def db_exists() -> bool:
    """Return True when the database file is present and non-empty."""
    p = Path(DB_PATH)
    return p.exists() and p.stat().st_size > 0
