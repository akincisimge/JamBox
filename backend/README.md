# JamBox API

FastAPI backend for JamBox rooms, members, Spotify sessions, real-time events,
queues, chat, and games.

## Synchronized Spotify playback

Room playback state is stored in PostgreSQL and distributed through the room
WebSocket. Every listener uses their own authenticated Spotify Web Playback SDK
device, so Spotify Premium and the OAuth scopes `streaming`,
`user-read-playback-state`, and `user-modify-playback-state` are required.
Browsers require each listener to enable audio once after entering a room.

## Run locally

From the repository root:

```bash
docker compose up --build
```

The API will be available at:

- API: `http://localhost:8000`
- Health: `http://localhost:8000/api/health`
- Swagger: `http://localhost:8000/docs`

## Room API development flow

1. Create or update a user with `POST /api/users`.
2. Copy the returned `id`.
3. For protected room endpoints, enter that UUID in the `X-User-Id` header.
4. Create a room with `POST /api/rooms`.
5. Share the returned `JAM-XXXXXX` code with another user.

The explicit header is temporary. Spotify server-side authentication will
replace it with a secure session in the authentication milestone.

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
