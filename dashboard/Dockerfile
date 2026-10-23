FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/dashboard
USER 10001:10001
EXPOSE 6111
CMD ["gunicorn", "--bind", "0.0.0.0:6111", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "dashboard.app:app"]
