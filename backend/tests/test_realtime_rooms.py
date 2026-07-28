from unittest.mock import AsyncMock

import pytest

from app.realtime.rooms import RoomConnectionManager


@pytest.mark.asyncio
async def test_room_connection_manager_broadcasts_and_disconnects() -> None:
    manager = RoomConnectionManager()
    websocket = AsyncMock()

    await manager.connect("jam-test12", websocket)
    await manager.broadcast("JAM-TEST12", {"type": "room_updated"})
    manager.disconnect("JAM-TEST12", websocket)

    websocket.accept.assert_awaited_once()
    websocket.send_json.assert_awaited_once_with({"type": "room_updated"})
    assert "JAM-TEST12" not in manager._connections
