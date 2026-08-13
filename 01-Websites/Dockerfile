# Dockerfile - runs any dynamic app on Render (free), your Oracle VM (free), or anywhere.
# Drop in the root of a Flask/Node/Go/PHP app, or replace the COPY lines with your app.
FROM python:3.12-slim

WORKDIR /app

# --- your app's dependencies ---
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .

# health check endpoint the platform pings
RUN mkdir -p /app && printf '{"ok":true,"uptime":"up"}' > /app/health.json

ENV PORT=8080
EXPOSE 8080

# --- change to your start command, e.g. gunicorn -b 0.0.0.0:8080 app:app ---
CMD ["python", "-m", "http.server", "8080"]
