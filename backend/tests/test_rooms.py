import re
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.room import PlaybackUpdate
from app.services.errors import ForbiddenError
from app.services.rooms import (
    generate_room_code,
    get_room,
    update_music_permission,
    update_playback,
)


def test_room_code_format() -> None:
    codes = {generate_room_code() for _ in range(100)}

    assert len(codes) == 100
    assert all(re.fullmatch(r"JAM-[A-Z0-9]{6}", code) for code in codes)


def test_room_routes_are_documented() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert "/api/users" in schema["paths"]
    assert "/api/rooms" in schema["paths"]
    assert "/api/rooms/{code}/join" in schema["paths"]
    assert "/api/rooms/{code}/leave" in schema["paths"]
    assert "/api/rooms/{code}/members/{user_id}/music-permission" in schema["paths"]
    assert "/api/rooms/{code}/playback" in schema["paths"]


@pytest.mark.asyncio
async def test_get_room_refreshes_previously_loaded_members() -> None:
    room = SimpleNamespace()
    session = SimpleNamespace(scalar=AsyncMock(return_value=room))

    result = await get_room(session, "jam-34ch9c")

    statement = session.scalar.await_args.args[0]
    assert statement.get_execution_options()["populate_existing"] is True
    assert result is room


@pytest.mark.asyncio
async def test_participant_cannot_change_music_permission() -> None:
    owner_id = uuid.uuid4()
    participant_id = uuid.uuid4()
    room = SimpleNamespace(owner_id=owner_id)
    participant = SimpleNamespace(id=participant_id)
    session = AsyncMock()

    with pytest.raises(
        ForbiddenError,
        match="Müzik yetkisini yalnızca oda sahibi değiştirebilir.",
    ):
        await update_music_permission(
            session,
            room,
            participant,
            participant_id,
            can_control_music=False,
        )

    session.get.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_member_without_permission_cannot_control_playback() -> None:
    room_id = uuid.uuid4()
    user_id = uuid.uuid4()
    room = SimpleNamespace(id=room_id)
    user = SimpleNamespace(id=user_id)
    membership = SimpleNamespace(can_control_music=False)
    session = AsyncMock()
    session.get.return_value = membership
    payload = PlaybackUpdate(
        spotify_uri="spotify:track:test",
        spotify_track_id="test",
        queue_uris=["spotify:track:test"],
        title="Test Track",
        artist="Test Artist",
        duration_ms=180_000,
        position_ms=0,
        is_playing=True,
    )

    with pytest.raises(
        ForbiddenError,
        match="Bu kullanıcının müzik kontrol yetkisi yok.",
    ):
        await update_playback(session, room, user, payload)

    session.commit.assert_not_awaited()
