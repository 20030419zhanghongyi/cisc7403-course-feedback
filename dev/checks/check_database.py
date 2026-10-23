"""Read the real database through the dashboard connection module."""

import json
import sys

import psycopg

from dashboard.db import connect


def main():
    try:
        with connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, difficulty, topic FROM public.feedback ORDER BY id")
                records = cursor.fetchall()
                cursor.execute("SHOW transaction_read_only")
                read_only = cursor.fetchone()[0]
        print(json.dumps({"connection": "ok", "read_only": read_only,
                          "record_count": len(records), "records": records}, indent=2))
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    except psycopg.Error:
        # Never print connection strings or server error details containing credentials.
        print("Database check failed. Check configuration, database readiness and schema.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
