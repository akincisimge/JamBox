# Step 2: Backend foundation

## Added

- FastAPI application factory and `/api/health` endpoint
- environment-based configuration and CORS
- asynchronous SQLAlchemy engine and session factory
- PostgreSQL `users`, `rooms`, and `room_members` models
- simple room permissions: `is_owner` and `can_control_music`
- Alembic configuration and initial migration
- Dockerfile and Docker Compose services for the API and PostgreSQL
- backend unit test and Ruff configuration

## Validation

- Ruff: passed
- Pytest: 1 passed
- Alembic offline migration generation: passed
- Frontend ESLint: passed with four existing image optimization warnings
- Frontend production build and artifact validation: passed
- Frontend rendered HTML test: passed

Docker is not installed in the execution environment, so the Compose runtime
was not started here. The Compose file uses the tested application command and
the official PostgreSQL image.
