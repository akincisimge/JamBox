# JamBox API

FastAPI backend for JamBox rooms, members, Spotify sessions, real-time events,
queues, chat, and games.

## Run locally

From the repository root:

```bash
docker compose up --build
```

The API will be available at:

- API: `http://localhost:8000`
- Health: `http://localhost:8000/api/health`
- Swagger: `http://localhost:8000/docs`

Apply migrations:

```bash
docker compose exec api alembic upgrade head
```

## Run without Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

When PostgreSQL runs directly on your computer, change the database host in
`.env` from `db` to `localhost`.

## Checks

```bash
ruff check .
pytest
alembic check
```
