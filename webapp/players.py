import json
import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    ronovo_sub TEXT PRIMARY KEY,
    progress TEXT NOT NULL,
    saved_at REAL NOT NULL
);
"""


class Players:
    """Range progress kept for each Ronovo account, so it follows the player to other browsers."""

    def __init__(self, path: str):
        self.path = path
        with self._db() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript(SCHEMA)

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def load(self, sub: str) -> tuple[dict, float] | None:
        with self._db() as db:
            row = db.execute("SELECT progress, saved_at FROM players WHERE ronovo_sub = ?", (sub,)).fetchone()
        return (json.loads(row[0]), row[1]) if row else None

    def store(self, sub: str, progress: dict, saved_at: float) -> None:
        with self._db() as db:
            db.execute(
                """INSERT INTO players (ronovo_sub, progress, saved_at) VALUES (?, ?, ?)
                   ON CONFLICT (ronovo_sub) DO UPDATE SET progress = excluded.progress, saved_at = excluded.saved_at
                   WHERE excluded.saved_at >= players.saved_at""",
                (sub, json.dumps(progress), saved_at),
            )
