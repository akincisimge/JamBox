import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes.tek_kart import _broadcast
from app.games.tek_kart import TekKartCard, TekKartPlayerState, TekKartState
from app.main import app
from app.schemas.tek_kart import TekKartGameResponse
from app.services.errors import ConflictError, NotFoundError
from app.services.tek_kart import (
    _game_response,
    _state_from_dict,
    _state_to_dict,
    join_tek_kart_game,
)


def make_user(user_id: uuid.UUID, name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        spotify_id=name,
        display_name=name,
        email=f"{name}@example.com",
        avatar_url=None,
        created_at="2026-01-01T00:00:00Z",
    )


def test_tek_kart_routes_are_documented() -> None:
    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]

    expected = {
        "/api/rooms/{code}/tek-kart",
        "/api/rooms/{code}/tek-kart/join",
        "/api/rooms/{code}/tek-kart/start",
        "/api/rooms/{code}/tek-kart/play",
        "/api/rooms/{code}/tek-kart/draw",
        "/api/rooms/{code}/tek-kart/call",
        "/api/rooms/{code}/tek-kart/restart",
    }
    assert expected.issubset(paths)


def test_state_round_trip_preserves_private_game_state() -> None:
    state = TekKartState(
        players=[
            TekKartPlayerState(
                "one",
                [TekKartCard("red-2-1", "number", "red", 2)],
                called_tek_kart=True,
            ),
            TekKartPlayerState(
                "two",
                [TekKartCard("wild-1", "wild")],
            ),
        ],
        draw_pile=[TekKartCard("blue-3-1", "number", "blue", 3)],
        discard_pile=[TekKartCard("yellow-5-1", "number", "yellow", 5)],
        active_color="green",
        turn_index=1,
        direction=-1,
    )

    restored = _state_from_dict(_state_to_dict(state))

    assert restored.players[0].hand[0].id == "red-2-1"
    assert restored.players[0].called_tek_kart
    assert restored.players[1].hand[0].kind == "wild"
    assert restored.draw_pile[0].id == "blue-3-1"
    assert restored.discard_pile[0].id == "yellow-5-1"
    assert restored.active_color == "green"
    assert restored.turn_index == 1
    assert restored.direction == -1


def test_response_reveals_only_viewers_hand() -> None:
    player_one_id = uuid.uuid4()
    player_two_id = uuid.uuid4()
    state = TekKartState(
        players=[
            TekKartPlayerState(
                str(player_one_id),
                [TekKartCard("red-2-1", "number", "red", 2)],
            ),
            TekKartPlayerState(
                str(player_two_id),
                [TekKartCard("wild-1", "wild")],
            ),
        ],
        draw_pile=[TekKartCard("blue-3-1", "number", "blue", 3)],
        discard_pile=[TekKartCard("red-5-1", "number", "red", 5)],
        active_color="red",
    )
    game = SimpleNamespace(
        id=uuid.uuid4(),
        creator_id=player_one_id,
        status="active",
        version=4,
        winner_user_id=None,
        state=_state_to_dict(state),
        player_one_user_id=player_one_id,
        player_two_user_id=player_two_id,
        player_three_user_id=None,
        player_four_user_id=None,
        player_one_user=make_user(player_one_id, "one"),
        player_two_user=make_user(player_two_id, "two"),
        player_three_user=None,
        player_four_user=None,
    )

    response = _game_response(game, player_one_id)

    assert [card.id for card in response.hand] == ["red-2-1"]
    assert response.players[1].hand_count == 1
    serialized = response.model_dump(mode="json")
    assert "wild-1" not in str(serialized)
    assert "blue-3-1" not in str(serialized)


@pytest.mark.asyncio
async def test_non_member_cannot_join() -> None:
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=uuid.uuid4())
    session = AsyncMock()
    session.get.return_value = None

    with pytest.raises(NotFoundError, match="Kullanıcı bu odada değil"):
        await join_tek_kart_game(session, room, actor)


@pytest.mark.asyncio
async def test_fifth_player_cannot_join() -> None:
    actor = SimpleNamespace(id=uuid.uuid4())
    room = SimpleNamespace(id=uuid.uuid4())
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=actor.id)
    player_ids = [uuid.uuid4() for _ in range(4)]
    game = SimpleNamespace(
        status="waiting",
        player_one_user_id=player_ids[0],
        player_two_user_id=player_ids[1],
        player_three_user_id=player_ids[2],
        player_four_user_id=player_ids[3],
    )

    with (
        patch("app.services.tek_kart._load_game", AsyncMock(return_value=game)),
        pytest.raises(ConflictError, match="dolu"),
    ):
        await join_tek_kart_game(session, room, actor)


@pytest.mark.asyncio
async def test_websocket_payload_contains_no_private_state() -> None:
    game = TekKartGameResponse(
        id=uuid.uuid4(),
        creator_id=uuid.uuid4(),
        status="active",
        version=8,
        turn_user_id=None,
        winner_user_id=None,
        active_color="blue",
        direction=1,
        draw_pile_count=73,
        top_card=None,
        hand=[],
        playable_card_ids=[],
        can_draw=False,
        can_call_tek_kart=False,
        called_tek_kart=False,
        players=[],
    )

    with patch("app.api.routes.tek_kart.room_connections.broadcast", AsyncMock()) as broadcast:
        await _broadcast("JAM-TEST", game)

    payload = broadcast.await_args.args[1]
    assert payload == {
        "type": "tek_kart_updated",
        "room_code": "JAM-TEST",
        "game_id": str(game.id),
        "version": 8,
    }
    assert "hand" not in payload
    assert "state" not in payload
    assert "cards" not in payload
