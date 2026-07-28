from collections import defaultdict

from fastapi import WebSocket


class RoomConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, code: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[code.upper()].add(websocket)

    def disconnect(self, code: str, websocket: WebSocket) -> None:
        room_connections = self._connections.get(code.upper())
        if room_connections is None:
            return

        room_connections.discard(websocket)
        if not room_connections:
            self._connections.pop(code.upper(), None)

    async def broadcast(self, code: str, event: dict[str, str]) -> None:
        room_code = code.upper()
        stale_connections: list[WebSocket] = []

        for websocket in tuple(self._connections.get(room_code, ())):
            try:
                await websocket.send_json(event)
            except RuntimeError:
                stale_connections.append(websocket)

        for websocket in stale_connections:
            self.disconnect(room_code, websocket)


room_connections = RoomConnectionManager()
