"""Background data refresh — runs every REFRESH_INTERVAL_S seconds."""
import threading
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from config import REFRESH_INTERVAL_S
import fetcher, store

_lock      = threading.Lock()
_last_run  = None
_scheduler = None


def _refresh():
    """Fetch all disease areas and upsert into the database."""
    global _last_run
    with _lock:
        try:
            rows = fetcher.fetch_all_disease_areas()
            store.upsert_trials(rows)
            _last_run = datetime.datetime.now()
            print(f"[scheduler] Refresh complete. {len(rows)} trials stored.")
        except Exception as exc:
            print(f"[scheduler] Refresh failed: {exc}")


def start() -> None:
    """Initialise DB, kick off first fetch in background, then schedule repeats."""
    global _scheduler
    store.init_db()
    threading.Thread(target=_refresh, daemon=True).start()
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _refresh,
        "interval",
        seconds=REFRESH_INTERVAL_S,
        id="data_refresh",
        max_instances=1,
    )
    _scheduler.start()


def force_refresh() -> None:
    """Trigger an immediate off-schedule refresh (called by the Refresh Now button)."""
    threading.Thread(target=_refresh, daemon=True).start()


def last_run_str() -> str:
    """Return a human-readable string describing how long ago the last refresh ran."""
    if _last_run is None:
        return "Fetching data..."
    delta = datetime.datetime.now() - _last_run
    mins  = int(delta.total_seconds() // 60)
    secs  = int(delta.total_seconds() % 60)
    if mins == 0:
        return f"Updated {secs}s ago"
    return f"Updated {mins}m {secs}s ago"
