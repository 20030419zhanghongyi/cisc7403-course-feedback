"""Shared PostgreSQL connection setup for the dashboard."""

import os

import psycopg


def connect():
    """Open a short-lived, read-only connection using the agreed environment."""
    names = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise ValueError("Missing database configuration: " + ", ".join(missing))
    try:
        port = int(os.environ["DB_PORT"])
    except ValueError:
        raise ValueError("DB_PORT must be an integer between 1 and 65535") from None
    if not 1 <= port <= 65535:
        raise ValueError("DB_PORT must be an integer between 1 and 65535")
    if os.environ["DB_PASSWORD"] == "CHANGE_ME_LOCAL_ONLY":
        raise ValueError("Replace the example DB_PASSWORD in your local .env")
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=port,
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
        options="-c default_transaction_read_only=on -c statement_timeout=5000",
    )
