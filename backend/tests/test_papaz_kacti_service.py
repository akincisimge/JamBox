import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.games.cards import Card
from app.games.papaz_kacti import (
    PapazKactiState,
    PapazKactiPlayerState,
)
from app.main import app
from app.services.errors import ConflictError, ForbiddenError, NotFoundError
from app.services.papaz_kacti import (
    _state_from_dict,
    _state_to_dict,
    join_papaz_kacti_game,
    start_papaz_kacti_game,
    draw_papaz_kacti_card,
    restart_papaz_kacti_game,
)


def test_papaz_kacti_routes_are_documented() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert "/api/rooms/{code}/papaz-kacti" in schema["paths"]
    assert "/api/rooms/{code}/papaz-kacti/join" in schema["paths"]
    assert "/api/rooms/{code}/papaz-kacti/start" in schema["paths"]
    assert "/api/rooms/{code}/papaz-kacti/draw" in schema["paths"]
    assert "/api/rooms/{code}/papaz-kacti/restart" in schema["paths"]


def test_state_serialization() -> None:
    state = PapazKactiState(
        players=[
            PapazKactiPlayerState("u1", hand=[Card("spades", "A")]),
            PapazKactiPlayerState("u2", is_finished=True),
        ],
        turn_index=1,
        status="active",
        loser_user_id="u2",
    )
    restored = _state_from_dict(_state_to_dict(state))

    assert restored.players[0].hand[0].id == "A-spades"
    assert restored.players[1].is_finished is True
    assert restored.turn_index == 1
    assert restored.status == "active"
    assert restored.loser_user_id == "u2"


@pytest.mark.asyncio
async def test_non_member_cannot_join() -> None:
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=uuid.uuid4())
    session = AsyncMock()
    session.get.return_value = None  # Not a member

    with pytest.raises(NotFoundError, match="Kullanıcı bu odada değil."):
        await join_papaz_kacti_game(session, room, actor)


@pytest.mark.asyncio
async def test_join_papaz_kacti_full_game() -> None:
    creator_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=uuid.uuid4())
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=actor.id)
    
    game = SimpleNamespace(
        status="waiting",
        player_one_user_id=creator_id,
        player_two_user_id=uuid.uuid4(),
        player_three_user_id=uuid.uuid4(),
        player_four_user_id=uuid.uuid4(),
    )

    with patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)):
        with pytest.raises(ConflictError, match="Oyun dolu"):
            await join_papaz_kacti_game(session, room, actor)


@pytest.mark.asyncio
async def test_start_game_not_creator() -> None:
    creator_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=actor_id)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=actor_id)
    
    game = SimpleNamespace(
        status="waiting",
        creator_id=creator_id,
        player_one_user_id=creator_id,
        player_two_user_id=actor_id,
        player_three_user_id=None,
        player_four_user_id=None,
    )

    with patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)):
        with pytest.raises(ForbiddenError, match="Oyunu sadece masayı açan başlatabilir."):
            await start_papaz_kacti_game(session, room, actor)


@pytest.mark.asyncio
async def test_draw_card_not_in_game() -> None:
    actor_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=actor_id)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=actor_id)
    
    game = SimpleNamespace(
        status="active",
        state={"status": "active", "players": []},
        player_one_user_id=uuid.uuid4(),
        player_two_user_id=uuid.uuid4(),
        player_three_user_id=None,
        player_four_user_id=None,
    )

    with patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)):
        with pytest.raises(ForbiddenError, match="Bu oyundaki oyunculardan biri değilsiniz."):
            await draw_papaz_kacti_card(session, room, actor, 0)


@pytest.mark.asyncio
async def test_draw_card_invalid_index() -> None:
    actor_id = uuid.uuid4()
    p2_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=actor_id)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=actor_id)
    
    state = PapazKactiState(
        players=[
            PapazKactiPlayerState(str(actor_id), hand=[Card("spades", "2")]),
            PapazKactiPlayerState(str(p2_id), hand=[Card("hearts", "2")]),
        ],
        turn_index=0,
        status="active"
    )
    
    game = SimpleNamespace(
        status="active",
        state=_state_to_dict(state),
        player_one_user_id=actor_id,
        player_two_user_id=p2_id,
        player_three_user_id=None,
        player_four_user_id=None,
    )

    with patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)):
        # Invalid index 5 (only 1 card in target's hand)
        with pytest.raises(ConflictError, match="Geçersiz kart indeksi."):
            await draw_papaz_kacti_card(session, room, actor, 5)


@pytest.mark.asyncio
async def test_restart_game_active_fails() -> None:
    creator_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=creator_id)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=creator_id)
    
    game = SimpleNamespace(
        status="active",
        creator_id=creator_id,
        player_one_user_id=creator_id,
        player_two_user_id=uuid.uuid4(),
        player_three_user_id=None,
        player_four_user_id=None,
    )

    with patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)):
        with pytest.raises(ConflictError, match="Oyun henüz bitmedi."):
            await restart_papaz_kacti_game(session, room, actor)


@pytest.mark.asyncio
async def test_restart_game_not_creator_fails() -> None:
    creator_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=actor_id)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=actor_id)
    
    game = SimpleNamespace(
        status="finished",
        creator_id=creator_id,
        player_one_user_id=creator_id,
        player_two_user_id=actor_id,
        player_three_user_id=None,
        player_four_user_id=None,
    )

    with patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)):
        with pytest.raises(ForbiddenError, match="Oyunu yalnızca masa sahibi yeniden başlatabilir."):
            await restart_papaz_kacti_game(session, room, actor)
