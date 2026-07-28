# JamBox

**Listen together. Play together.**

JamBox is a real-time social music room platform. Friends can join a private
room, listen together, shape a shared queue, chat, react, invite others, and
play lightweight multiplayer games without leaving the room.

## Current status

JamBox is currently a frontend prototype with a working first slice of Spotify
integration:

- Spotify OAuth with PKCE
- Spotify profile and playlist loading
- playlist track browsing
- create/join room interface
- demo room, chat, voting, and playback controls

Room membership, chat, queue voting, playback synchronization, permissions, and
games are still demo-only client state. They will be connected to the planned
FastAPI/WebSocket backend in the next milestones.

## Product rules

- A room creator is the room owner.
- The owner can grant music-control permission to selected participants.
- Everyone can invite friends, chat, react, suggest songs, vote, start games,
  and join games.
- Only the owner can remove participants or close the room.
- JamBox intentionally avoids a complex role hierarchy.

## Planned architecture

| Layer | Technology |
| --- | --- |
| Web client | Next.js, React, TypeScript |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM and migrations | SQLAlchemy, Alembic |
| Real-time transport | FastAPI WebSocket |
| Music | Spotify OAuth, Web API, Playback SDK |
| Testing | Pytest, Vitest |
| Delivery | Docker, GitHub Actions |

## Repository structure

```text
app/                 Next.js routes and application shell
components/ui/       Shared UI primitives
lib/spotify/         Spotify browser client and OAuth helpers
mocks/               Explicitly isolated prototype data
types/               Shared TypeScript domain types
db/                  Existing Cloudflare D1/Drizzle starter support
tests/               Build and rendering checks
```

The FastAPI application lives under `backend/`. It includes PostgreSQL models,
Alembic migrations, a health endpoint, tests, and Docker configuration.

## Local setup

Requirements:

- Node.js 22.13 or newer
- A Spotify developer application

Create the local environment file:

```bash
cp .env.example .env.local
```

Set the Spotify application values:

```env
NEXT_PUBLIC_SPOTIFY_CLIENT_ID=your_spotify_client_id
NEXT_PUBLIC_SPOTIFY_REDIRECT_URI=http://localhost:3000/callback
```

The redirect URI must also be registered in the Spotify developer dashboard.

Install and run:

```bash
npm ci
npm run dev
```

Start the backend and PostgreSQL in a second terminal:

```bash
docker compose up --build
```

Backend endpoints:

- Health: `http://localhost:8000/api/health`
- Swagger: `http://localhost:8000/docs`

## Commands

```bash
npm run dev
npm run lint
npm run build
npm test
```

## Delivery milestones

1. Refactor the prototype and isolate Spotify/domain code.
2. ✅ Add FastAPI, PostgreSQL, SQLAlchemy, Alembic, and Docker.
3. Implement Spotify sessions, room operations, invitations, and permissions.
4. Add WebSocket presence, chat, reactions, queue, and voting.
5. Add synchronized Spotify playback.
6. Add the multiplayer game engine and first game: Tic-Tac-Toe.
7. Add Connect Four, music quiz, session summaries, and shared playlists.

## MVP

The first usable release will include Spotify sign-in, real rooms, invite
links, live presence, chat, reactions, a shared queue, voting, simple
music-control permission, synchronized playback, and Tic-Tac-Toe.
