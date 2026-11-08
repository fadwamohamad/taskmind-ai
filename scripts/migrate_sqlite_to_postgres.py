"""One-shot SQLite -> PostgreSQL migration (local only, never executed in tests).

Copy rows from the project-root SQLite file to the URL in ``DATABASE_URL``
(e.g. Neon) using SQLModel. Preserves IDs, timestamps, and field values.
No data is deleted from the source; run explicitly only when PostgreSQL
is provisioned:

    DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require python scripts/migrate_sqlite_to_postgres.py

Caveats: SQLite/Postgres types map cleanly for this schema (TEXT/INTEGER/DATE/DATETIME).
Run on a quiesced app; do not run automatically on deploy.
"""

import os
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.pool import NullPool
from sqlmodel import Session, SQLModel, create_engine, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import normalize_database_url  # noqa: E402
from app.models import Task  # noqa: E402


def _source_url() -> str:
    root = Path(__file__).resolve().parents[1]
    return f"sqlite:///{(root / 'taskmind.db').as_posix()}"


def main() -> int:
    src_url = _source_url()
    dst_url_raw = os.getenv("DATABASE_URL", "")
    if not dst_url_raw or dst_url_raw.startswith("sqlite"):
        print(
            "Set DATABASE_URL to a PostgreSQL connection string.",
            file=sys.stderr,
        )
        return 2
    dst_url = normalize_database_url(dst_url_raw)
    src = create_engine(src_url, connect_args={"check_same_thread": False})
    dst = create_engine(dst_url, poolclass=NullPool, pool_pre_ping=True)
    SQLModel.metadata.create_all(dst)
    with Session(src) as s1, Session(dst) as s2:
        rows = s1.exec(select(Task)).all()
        for row in rows:
            existing = s2.get(Task, row.id)
            if existing is None:
                s2.add(Task.model_validate(row.model_dump()))
        s2.commit()
        if rows:
            s2.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence('task', 'id'), "
                    "COALESCE((SELECT MAX(id) FROM task), 1), true)"
                )
            )
            s2.commit()
        count = len(s2.exec(select(Task)).all())
    print(f"migrated {len(rows)} rows, destination now has {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
