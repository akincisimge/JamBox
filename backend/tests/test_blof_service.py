import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes.blof import _broadcast
from app.games.blof import BlofPlayerState, BlofState
from app.games.cards import Card
from app.main import app
from app.schemas.blof import BlofGameResponse
from app.services.blof import (
    _game_response,
    _state_from_dict,
    _state_to_dict,
    join_blof_game,
)
from app.services.errors import ConflictError, NotFoundError


def make_user(user_id: uuid.UUID, name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        spotify_id=name,
        display_name=name,
        email=f"{name}@example.com",
        avatar_url=None,
        created_at="2026-01-01T00:00:00Z",
    )


def test_blof_routes_are_documented() -> None:
    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]

    expected = {
        "/api/rooms/{code}/blof",
        "/api/rooms/{code}/blof/join",
        "/api/rooms/{code}/blof/start",
        "/api/rooms/{code}/blof/play",
        "/api/rooms/{code}/blof/call",
        "/api/rooms/{code}/blof/accept",
        "/api/rooms/{code}/blof/restart",
    }
    assert expected.issubset(paths)


def test_state_round_trip_preserves_private_game_state() -> None:
    state = BlofState(
        players=[
            BlofPlayerState("one", [Card("clubs", "2")]),
            BlofPlayerState("two", [Card("hearts", "K")]),
        ],
        turn_index=1,
        pile=[Card("spades", "A")],
        last_played_cards=[Card("spades", "A")],
        last_declared_rank="Q",
        last_player_user_id="one",
        pending_winner_user_id="one",
    )

    restored = _state_from_dict(_state_to_dict(state))
    assert restored.players[0].hand[0].id == "2-clubs"
    assert restored.players[1].hand[0].id == "K-hearts"
    assert restored.turn_index == 1
    assert restored.pile[0].id == "A-spades"
    assert restored.last_declared_rank == "Q"
    assert restored.pending_winner_user_id == "one"


def test_response_reveals_only_viewers_hand() -> None:
    player_one_id = uuid.uuid4()
    player_two_id = uuid.uuid4()
    state = BlofState(
        players=[
            BlofPlayerState(str(player_one_id), [Card("clubs", "2")]),
            BlofPlayerState(str(player_two_id), [Card("hearts", "K")]),
        ]
    )
    game = SimpleNamespace(
        id=uuid.uuid4(),
        creator_id=player_one_id,
        status="active",
        version=3,
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
    assert [card.id for card in response.hand] == ["2-clubs"]
    assert response.players[1].hand_count == 1
    assert not hasattr(response.players[1], "hand")
    serialized = response.model_dump(mode="json")
    assert "K-hearts" not in str(serialized)


@pytest.mark.asyncio
async def test_non_member_cannot_join() -> None:
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=uuid.uuid4())
    session = AsyncMock()
    session.get.return_value = None

    with pytest.raises(NotFoundError, match="Kullanıcı bu odada değil"):
        await join_blof_game(session, room, actor)


@pytest.mark.asyncio
async def test_fifth_player_cannot_join() -> None:
    actor = SimpleNamespace(id=uuid.uuid4())
    room = SimpleNamespace(id=uuid.uuid4())
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=actor.id)
    game = SimpleNamespace(
        status="waiting",
        player_one_user_id=uuid.uuid4(),
        player_two_user_id=uuid.uuid4(),
        player_three_user_id=uuid.uuid4(),
        player_four_user_id=uuid.uuid4(),
        player_one_user=make_user(uuid.uuid4(), "one"),
        player_two_user=make_user(uuid.uuid4(), "two"),
        player_three_user=make_user(uuid.uuid4(), "three"),
        player_four_user=make_user(uuid.uuid4(), "four"),
    )

    with (
        patch("app.services.blof._load_game", AsyncMock(return_value=game)),
        pytest.raises(ConflictError, match="dolu"),
    ):
        await join_blof_game(session, room, actor)


@pytest.mark.asyncio
async def test_websocket_payload_contains_no_private_state() -> None:
    game = BlofGameResponse(
        id=uuid.uuid4(),
        creator_id=uuid.uuid4(),
        status="active",
        version=9,
        turn_user_id=None,
        pending_winner_user_id=None,
        winner_user_id=None,
        pile_count=7,
        last_play_count=2,
        last_declared_rank="Q",
        last_player_user_id=None,
        hand=[],
        players=[],
        last_result=None,
    )

    with patch("app.api.routes.blof.room_connections.broadcast", AsyncMock()) as broadcast:
        await _broadcast("JAM-TEST", game)

    payload = broadcast.await_args.args[1]
    assert payload == {
        "type": "blof_updated",
        "room_code": "JAM-TEST",
        "game_id": str(game.id),
        "version": 9,
    }
    assert "hand" not in payload
    assert "state" not in payload
    assert "cards" not in payload
