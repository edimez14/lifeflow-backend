# Lifeflow Backend

Backend de Lifeflow con FastAPI, SQLAlchemy async, Alembic y SQLite persistente.

## Requisitos

- Python 3.11+
- Virtualenv activo
- Docker opcional para correr SQLite en contenedor

## Instalación

```bash
pip install -e ".[dev]"
```

## Variables de entorno

Configura el archivo [.env](.env) con estas variables:

- `DATABASE_URL`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_HOURS`
- `SERVER_HOST`
- `SERVER_PORT`
- `DEBUG`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `FIREBASE_CREDENTIALS_PATH`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_STORAGE_BUCKET`

## Base de datos

La base SQLite vive en [data/lifeflow.db](data/lifeflow.db) y se mantiene persistente.

## Ejecutar migraciones

```bash
alembic upgrade head
```

## Ejecutar el servidor

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Ejecutar tests

```bash
pytest
```

## Healthcheck

- `GET /health`

## WebSocket

- `ws://127.0.0.1:8000/ws/{workspace_id}`