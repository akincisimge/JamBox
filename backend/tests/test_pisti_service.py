import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.games.pisti import Card, PistiState, PlayerState
from app.main import app
from app.services.errors import ConflictError
from app.services.pisti import (
    _state_from_dict,
    _state_to_dict,
    join_pisti_game,
    make_pisti_move,
)


def test_pisti_routes_are_documented() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert "/api/rooms/{code}/pisti" in schema["paths"]
    assert "/api/rooms/{code}/pisti/join" in schema["paths"]
    assert "/api/rooms/{code}/pisti/cards" in schema["paths"]
    assert "/api/rooms/{code}/pisti/restart" in schema["paths"]


def test_pisti_state_round_trip_preserves_cards_and_turn() -> None:
    state = PistiState(
        players=[
            PlayerState("simge", hand=[Card("spades", "A")]),
            PlayerState("friend", captured=[Card("clubs", "2")], pisti_count=1),
        ],
        deck=[Card("hearts", "K")],
        table=[Card("diamonds", "10")],
        turn_index=1,
        last_capturer_index=0,
    )

    restored = _state_from_dict(_state_to_dict(state))

    assert restored.players[0].hand[0].id == "A-spades"
    assert restored.players[1].captured[0].id == "2-clubs"
    assert restored.players[1].pisti_count == 1
    assert restored.deck[0].id == "K-hearts"
    assert restored.table[0].id == "10-diamonds"
    assert restored.turn_index == 1
    assert restored.last_capturer_index == 0


@pytest.mark.asyncio
async def test_creator_cannot_accept_own_pisti_invite() -> None:
    creator_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    creator = SimpleNamespace(id=creator_id)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=creator_id)
    game = SimpleNamespace(status="waiting", player_one_user_id=creator_id)

    with (
        patch("app.services.pisti._load_game", AsyncMock(return_value=game)),
        pytest.raises(ConflictError, match="Kendi Pişti davetinize")
    ):
        await join_pisti_game(session, room, creator)

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_pisti_move_updates_serialized_state() -> None:
    player_one_id = uuid.uuid4()
    player_two_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    player_one = SimpleNamespace(id=player_one_id)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=player_one_id)
    state = PistiState(
        players=[
            PlayerState(str(player_one_id), hand=[Card("spades", "7")]),
            PlayerState(str(player_two_id), hand=[Card("clubs", "3")]),
        ],
        deck=[],
        table=[Card("hearts", "7")],
    )
    game = SimpleNamespace(
        status="active",
        state=_state_to_dict(state),
        player_one_user_id=player_one_id,
        player_two_user_id=player_two_id,
        scores={},
        winner_user_id=None,
    )

    with (
        patch("app.services.pisti._load_game", AsyncMock(return_value=game)),
        patch("app.services.pisti._game_response", return_value="response"),
    ):
        result = await make_pisti_move(session, room, player_one, "7-spades")

    stored = _state_from_dict(game.state)
    assert result == "response"
    assert stored.table == []
    assert len(stored.players[0].captured) == 2
    assert stored.players[0].pisti_count == 1
    session.commit.assert_awaited_once()
