"""Read-only course feedback dashboard."""
import psycopg
from flask import Flask, render_template
from .stats import get_summary

app = Flask(__name__)


@app.get('/')
def index():
    try:
        summary = get_summary()
    except (psycopg.Error, ValueError):
        # Deliberately omit exceptions/connection details from logs and responses.
        app.logger.error('Dashboard database query unavailable')
        return render_template('index.html', summary=None, unavailable=True), 503
    return render_template('index.html', summary=summary, unavailable=False)


@app.after_request
def prevent_stale_results(response):
    response.headers['Cache-Control'] = 'no-store'
    return response
