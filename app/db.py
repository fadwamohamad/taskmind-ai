import os
from typing import Generator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlmodel import Session, SQLModel, create_engine


def normalize_database_url(url: str) -> str:
    if not url or url.startswith("sqlite"):
        return url
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme in ("postgres", "postgresql"):
        parsed = parsed._replace(scheme="postgresql+psycopg")
    elif scheme == "postgresql+psycopg":
        pass
    else:
        return url
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if "sslmode" not in query and "ssl" not in query:
        query["sslmode"] = "require"
    return urlunparse(parsed._replace(query=urlencode(query)))


DATABASE_URL = normalize_database_url(
    os.getenv("DATABASE_URL", "sqlite:///./taskmind.db")
)

is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
engine_kwargs = {}
if not is_sqlite:
    # Serverless-friendly: each invocation gets a fresh connection; avoid pooling.
    try:
        from sqlalchemy.pool import NullPool

        engine_kwargs["poolclass"] = NullPool
    except Exception:
        pass
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)


def create_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
