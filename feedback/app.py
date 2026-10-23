import os
import logging

import psycopg
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

VALID_TOPICS = {
    "Virtual Machine",
    "Docker",
    "Kubernetes",
    "Serverless",
}


def get_db_connection():
    """Connect to PostgreSQL using environment variables."""

    required_vars = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing = [
        name for name in required_vars
        if not os.environ.get(name)
    ]

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )

    try:
        port = int(os.environ["DB_PORT"])
    except ValueError as exc:
        raise RuntimeError("DB_PORT must be an integer") from exc

    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=port,
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )


def render_form(error=None, success=False, status=200):
    """Render feedback page."""
    return (
        render_template(
            "index.html",
            error=error,
            success=success,
            selected_difficulty="",
            selected_topic="",
        ),
        status,
    )


@app.route("/", methods=["GET", "POST"])
def feedback():
    if request.method == "GET":
        success = request.args.get("success") == "1"
        return render_template(
            "index.html",
            error=None,
            success=success,
            selected_difficulty="",
            selected_topic="",
        )

    difficulty_text = request.form.get("difficulty", "").strip()
    topic = request.form.get("topic", "").strip()

    try:
        difficulty = int(difficulty_text)
    except (ValueError, TypeError):
        return render_form(
            error="Invalid difficulty. Please choose a value from 1 to 5.",
            status=400,
        )

    if difficulty < 1 or difficulty > 5:
        return render_form(
            error="Difficulty must be between 1 and 5.",
            status=400,
        )

    if topic not in VALID_TOPICS:
        return render_form(
            error="Invalid topic. Please choose one of the listed topics.",
            status=400,
        )

    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO public.feedback (difficulty, topic)
                VALUES (%s, %s)
                """,
                (difficulty, topic),
            )

    except (psycopg.Error, RuntimeError, OSError):
        app.logger.exception(
            "Feedback submission failed: database operation unsuccessful"
        )

        return render_form(
            error=(
                "Feedback could not be saved because the database "
                "is unavailable. Please try again later."
            ),
            status=503,
        )

    app.logger.info(
        "Feedback submitted successfully: difficulty=%d, topic=%s",
        difficulty,
        topic,
    )

    return redirect(url_for("feedback", success="1"), code=303)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6110)
