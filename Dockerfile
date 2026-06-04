# Manajemen Mahasiswa — Flet web app served via uvicorn (ASGI).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Excel "database" lives here; mount a persistent volume at /app/data in Dokploy
# so added students survive restarts/redeploys. db.py auto-creates + seeds it.
RUN mkdir -p /app/data
VOLUME ["/app/data"]

EXPOSE 8550

# Production server. Flet's ASGI app is exported in asgi.py (no_cdn=True).
CMD ["python", "-m", "uvicorn", "asgi:app", "--host", "0.0.0.0", "--port", "8550"]
