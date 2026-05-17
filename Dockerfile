# Lifeflow Backend Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Copy deps and app, install everything
COPY pyproject.toml .
COPY app/ ./app/
RUN pip install --no-cache-dir .

# Copy migrations config
COPY migrations/ ./migrations/
COPY alembic.ini .

# Data dir for SQLite persistence
RUN mkdir -p /app/data

EXPOSE 8000

# Auto-migrate then start
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
