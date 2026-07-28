import re

from fastapi.testclient import TestClient

from app.main import app
from app.services.rooms import generate_room_code


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
