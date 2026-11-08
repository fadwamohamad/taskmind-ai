import os

from app.db import DATABASE_URL, normalize_database_url


def test_sqlite_remains_default():
    assert DATABASE_URL.startswith("sqlite")
    assert normalize_database_url("sqlite:///./taskmind.db") == "sqlite:///./taskmind.db"


def test_postgresql_prefix_normalized():
    assert normalize_database_url("postgresql://u:p@h/db").startswith("postgresql+psycopg://")
    assert normalize_database_url("postgres://u:p@h/db").startswith("postgresql+psycopg://")
    assert normalize_database_url("postgresql+psycopg://u:p@h/db").startswith("postgresql+psycopg://")


def test_sslmode_required_by_default_and_not_duplicated():
    out = normalize_database_url("postgresql://u:p@h/db")
    assert "sslmode=require" in out
    out2 = normalize_database_url("postgresql://u:p@h/db?sslmode=disable")
    assert "sslmode=disable" in out2
    assert out2.count("sslmode") == 1


def test_query_params_preserved(monkeypatch):
    out = normalize_database_url("postgresql://u:p@h/db?application_name=x")
    assert "application_name=x" in out
    assert "sslmode=require" in out
