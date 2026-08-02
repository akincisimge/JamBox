import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.games.cards import Card
from app.games.papaz_kacti import (
    PapazKactiPlayerState,
    PapazKactiState,
)
from app.main import app
from app.services.errors import ConflictError, ForbiddenError, NotFoundError
from app.services.papaz_kacti import (
    _state_from_dict,
    _state_to_dict,
    draw_papaz_kacti_card,
    join_papaz_kacti_game,
    restart_papaz_kacti_game,
    start_papaz_kacti_game,
)


def make_test_user(user_id: uuid.UUID, name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        display_name=name,
        spotify_id=name,
        email=f"{name}@a.com",
        avatar_url="url",
        created_at="2023-01-01T00:00:00Z",
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
        id=uuid.uuid4(),
        status="waiting",
        player_one_user_id=creator_id,
        player_two_user_id=uuid.uuid4(),
        player_three_user_id=uuid.uuid4(),
        player_four_user_id=uuid.uuid4(),
    )

    with (
        patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)),
        pytest.raises(ConflictError, match="Oyun dolu")
    ):
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
        id=uuid.uuid4(),
        status="waiting",
        creator_id=creator_id,
        player_one_user_id=creator_id,
        player_two_user_id=actor_id,
        player_three_user_id=None,
        player_four_user_id=None,
    )

    with (
        patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)),
        pytest.raises(ForbiddenError, match="Oyunu sadece masayı açan başlatabilir.")
    ):
        await start_papaz_kacti_game(session, room, actor)


@pytest.mark.asyncio
async def test_draw_card_not_in_game() -> None:
    actor_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=actor_id)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=actor_id)
    
    game = SimpleNamespace(
        id=uuid.uuid4(),
        status="active",
        state={"status": "active", "players": []},
        player_one_user_id=uuid.uuid4(),
        player_two_user_id=uuid.uuid4(),
        player_three_user_id=None,
        player_four_user_id=None,
    )

    with (
        patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)),
        pytest.raises(ForbiddenError, match="Bu oyundaki oyunculardan biri değilsiniz.")
    ):
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
        id=uuid.uuid4(),
        status="active",
        state=_state_to_dict(state),
        player_one_user_id=actor_id,
        player_two_user_id=p2_id,
        player_three_user_id=None,
        player_four_user_id=None,
    )

    with (
        patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)),
        pytest.raises(ConflictError, match="Geçersiz kart indeksi.")
    ):
        await draw_papaz_kacti_card(session, room, actor, 5)


@pytest.mark.asyncio
async def test_restart_game_active_fails() -> None:
    creator_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=creator_id)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=creator_id)
    
    game = SimpleNamespace(
        id=uuid.uuid4(),
        status="active",
        creator_id=creator_id,
        player_one_user_id=creator_id,
        player_two_user_id=uuid.uuid4(),
        player_three_user_id=None,
        player_four_user_id=None,
    )

    with (
        patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)),
        pytest.raises(ConflictError, match="Oyun henüz bitmedi.")
    ):
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
        id=uuid.uuid4(),
        status="finished",
        creator_id=creator_id,
        player_one_user_id=creator_id,
        player_two_user_id=actor_id,
        player_three_user_id=None,
        player_four_user_id=None,
    )

    with (
        patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)),
        pytest.raises(ForbiddenError, match="Oyunu yalnızca masa sahibi yeniden başlatabilir.")
    ):
        await restart_papaz_kacti_game(session, room, actor)

@pytest.mark.asyncio
async def test_draw_card_wrong_turn() -> None:
    actor_id = uuid.uuid4()
    p2_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=p2_id)  # actor is p2, but turn is 0 (p1)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=p2_id)

    state = PapazKactiState(
        players=[
            PapazKactiPlayerState(str(actor_id), hand=[Card("spades", "2")]),
            PapazKactiPlayerState(str(p2_id), hand=[Card("hearts", "2")]),
        ],
        turn_index=0,
        status="active"
    )

    game = SimpleNamespace(
        id=uuid.uuid4(),
        status="active",
        state=_state_to_dict(state),
        player_one_user_id=actor_id,
        player_two_user_id=p2_id,
        player_three_user_id=None,
        player_four_user_id=None,
    )

    with (
        patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)),
        pytest.raises(ConflictError, match="Hamle sırası bu oyuncuda değil.")
    ):
        await draw_papaz_kacti_card(session, room, actor, 0)

@pytest.mark.asyncio
async def test_get_game_state_hides_other_hands() -> None:
    from app.services.papaz_kacti import get_papaz_kacti_game
    actor_id = uuid.uuid4()
    p2_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=actor_id)
    session = AsyncMock()

    state = PapazKactiState(
        players=[
            PapazKactiPlayerState(str(actor_id), hand=[Card("spades", "2")]),
            PapazKactiPlayerState(str(p2_id), hand=[Card("hearts", "3")]),
        ],
        turn_index=0,
        status="active"
    )

    game = SimpleNamespace(
        id=uuid.uuid4(),
        status="active",
        state=_state_to_dict(state),
        player_one_user_id=actor_id,
        player_two_user_id=p2_id,
        player_three_user_id=None,
        player_four_user_id=None,
        creator_id=actor_id,
        loser_user_id=None,
        player_one_user=make_test_user(actor_id, "p1"),
        player_two_user=make_test_user(p2_id, "p2"),
        player_three_user=None,
        player_four_user=None,
    )

    with patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)):
        response = await get_papaz_kacti_game(session, room, actor)
        
        # Check that actor's hand is visible
        assert len(response.hand) == 1
        assert response.hand[0].suit == "spades"
        
        # Check that p2's hand is hidden (list of dicts or objects without suit/rank)
        assert response.hand_counts[str(p2_id)] == 1

@pytest.mark.asyncio
async def test_get_game_state_spectator_sees_no_hands() -> None:
    from app.services.papaz_kacti import get_papaz_kacti_game
    actor_id = uuid.uuid4()
    p1_id = uuid.uuid4()
    p2_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    actor = SimpleNamespace(id=actor_id) # Spectator
    session = AsyncMock()

    state = PapazKactiState(
        players=[
            PapazKactiPlayerState(str(p1_id), hand=[Card("spades", "2")]),
            PapazKactiPlayerState(str(p2_id), hand=[Card("hearts", "3")]),
        ],
        turn_index=0,
        status="active"
    )

    game = SimpleNamespace(
        id=uuid.uuid4(),
        status="active",
        state=_state_to_dict(state),
        player_one_user_id=p1_id,
        player_two_user_id=p2_id,
        player_three_user_id=None,
        player_four_user_id=None,
        creator_id=p1_id,
        loser_user_id=None,
        player_one_user=make_test_user(p1_id, "p1"),
        player_two_user=make_test_user(p2_id, "p2"),
        player_three_user=None,
        player_four_user=None,
    )

    with patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)):
        response = await get_papaz_kacti_game(session, room, actor)
        
        assert len(response.hand) == 0
        assert response.hand_counts[str(p1_id)] == 1
        assert response.hand_counts[str(p2_id)] == 1

@pytest.mark.asyncio
async def test_websocket_payload_no_state_leak() -> None:
    from fastapi.testclient import TestClient

    from app.api.dependencies import get_current_user, get_db_session
    from app.main import app
    
    actor_id = uuid.uuid4()
    p2_id = uuid.uuid4()
    actor = make_test_user(actor_id, "p1")
    
    async def mock_get_current_user():
        return actor
        
    async def mock_get_db_session():
        yield AsyncMock()
        
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_db_session] = mock_get_db_session
    
    game_response = SimpleNamespace(
        id=uuid.uuid4(),
        status="active",
        creator_id=actor_id,
        player_one_user_id=actor_id,
        player_two_user_id=p2_id,
        player_three_user_id=None,
        player_four_user_id=None,
        turn_user_id=actor_id,
        loser_user_id=None,
        hand=[],
        hand_counts={str(actor_id): 1, str(p2_id): 1},
        player_one_user=actor,
        player_two_user=make_test_user(p2_id, "p2"),
        player_three_user=None,
        player_four_user=None,
        model_dump=lambda **kwargs: {"status": "active"}
    )
    
    # We patch the service layer so the route logic executes
    with (
        patch(
            "app.api.routes.papaz_kacti.get_room",
            AsyncMock(return_value=SimpleNamespace(code="TEST12"))
        ),
        patch(
            "app.api.routes.papaz_kacti.start_papaz_kacti_game",
            AsyncMock(return_value=game_response)
        ),
        patch(
            "app.api.routes.papaz_kacti.room_connections.broadcast",
            AsyncMock()
        ) as mock_broadcast
    ):
        with TestClient(app) as client:
            response = client.post("/api/rooms/TEST12/papaz-kacti/start")
            
        assert response.status_code == 200
        
        mock_broadcast.assert_called_once_with(
            "TEST12",
            {"type": "papaz_kacti_updated"}
        )
        
        # Verify exactly no state in payload
        payload = mock_broadcast.call_args[0][1]
        assert payload == {"type": "papaz_kacti_updated"}
        assert "state" not in payload
        assert "hand" not in payload
        assert "hands" not in payload
        assert "cards" not in payload
        assert "players" not in payload

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_restart_game_success() -> None:
    creator_id = uuid.uuid4()
    p2_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4(), code="TEST12")
    actor = SimpleNamespace(id=creator_id)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=creator_id)

    game = SimpleNamespace(
        id=uuid.uuid4(),
        status="finished",
        state=None,
        player_one_user_id=creator_id,
        player_two_user_id=p2_id,
        player_three_user_id=None,
        player_four_user_id=None,
        creator_id=creator_id,
        loser_user_id=None,
        player_one_user=make_test_user(creator_id, "p1"),
        player_two_user=make_test_user(p2_id, "p2"),
        player_three_user=None,
        player_four_user=None,
    )

    with patch("app.services.papaz_kacti._load_game", AsyncMock(return_value=game)):
        response = await restart_papaz_kacti_game(session, room, actor)
        assert response.status == "active"
