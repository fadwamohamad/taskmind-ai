from sqlmodel import inspect

import app.models  # noqa: F401  # registers the Task table
from app.db import create_db, engine


def test_create_db_creates_task_table():
    create_db()
    table_names = inspect(engine).get_table_names()
    assert "task" in table_names
