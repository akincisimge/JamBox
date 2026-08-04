import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes.kelime_kapismasi import _broadcast
from app.games.kelime_kapismasi import start_game, submit_word, sync_state
from app.main import app
from app.schemas.kelime_kapismasi import KelimeKapismasiGameResponse
from app.services.errors import ConflictError
from app.services.kelime_kapismasi import (
    _build_rounds,
    _game_response,
    _state_from_dict,
    _state_to_dict,
    join_kelime_kapismasi_game,
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


def test_kelime_kapismasi_routes_are_documented() -> None:
    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]

    expected = {
        "/api/rooms/{code}/kelime-kapismasi",
        "/api/rooms/{code}/kelime-kapismasi/join",
        "/api/rooms/{code}/kelime-kapismasi/start",
        "/api/rooms/{code}/kelime-kapismasi/words",
        "/api/rooms/{code}/kelime-kapismasi/restart",
    }
    assert expected.issubset(paths)


def test_curated_rounds_match_the_six_stage_plan() -> None:
    rounds = _build_rounds()

    assert len(rounds) == 6
    assert [item.difficulty for item in rounds] == [
        "easy",
        "easy",
        "medium",
        "medium",
        "hard",
        "hard",
    ]
    assert all(item.valid_words for item in rounds)


def test_state_round_trip_preserves_private_submissions_and_results() -> None:
    now = datetime(2026, 8, 4, 10, 0, tzinfo=timezone.utc)
    state = start_game(["one", "two"], _build_rounds(), now=now)
    sync_state(state, now=now + timedelta(seconds=4))
    submit_word(state, "one", "kalem", now=now + timedelta(seconds=5))

    restored = _state_from_dict(_state_to_dict(state))

    assert restored.status == "playing"
    assert restored.players[0].submissions[0].word == "kalem"
    assert restored.players[0].submissions[0].submitted_at == now + timedelta(seconds=5)
    assert restored.rounds[0].valid_words == state.rounds[0].valid_words
    assert restored.phase_ends_at == state.phase_ends_at


def test_response_hides_opponents_words_during_active_stage() -> None:
    player_one_id = uuid.uuid4()
    player_two_id = uuid.uuid4()
    now = datetime(2026, 8, 4, 10, 0, tzinfo=timezone.utc)
    state = start_game(
        [str(player_one_id), str(player_two_id)],
        _build_rounds(),
        now=now,
    )
    sync_state(state, now=now + timedelta(seconds=4))
    submit_word(state, str(player_one_id), "kalem", now=now + timedelta(seconds=5))
    submit_word(state, str(player_two_id), "karamel", now=now + timedelta(seconds=6))

    game = SimpleNamespace(
        id=uuid.uuid4(),
        creator_id=player_one_id,
        status="playing",
        version=3,
        winner_user_id=None,
        state=_state_to_dict(state),
        player_one_user_id=player_one_id,
        player_two_user_id=player_two_id,
        player_one_user=make_user(player_one_id, "one"),
        player_two_user=make_user(player_two_id, "two"),
    )

    response = _game_response(game, player_one_id, now=now + timedelta(seconds=7))
    serialized = response.model_dump(mode="json")

    assert response.own_words == ["kalem"]
    assert response.players[1].current_word_count == 1
    assert "karamel" not in str(serialized)


@pytest.mark.asyncio
async def test_third_player_cannot_join_two_player_game() -> None:
    actor = SimpleNamespace(id=uuid.uuid4())
    room = SimpleNamespace(id=uuid.uuid4())
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=actor.id)
    game = SimpleNamespace(
        status="waiting",
        player_one_user_id=uuid.uuid4(),
        player_two_user_id=uuid.uuid4(),
    )

    with (
        patch(
            "app.services.kelime_kapismasi._load_game",
            AsyncMock(return_value=game),
        ),
        pytest.raises(ConflictError, match="iki kişiliktir"),
    ):
        await join_kelime_kapismasi_game(session, room, actor)


@pytest.mark.asyncio
async def test_websocket_payload_contains_no_words_or_private_state() -> None:
    game = KelimeKapismasiGameResponse(
        id=uuid.uuid4(),
        creator_id=uuid.uuid4(),
        status="playing",
        version=8,
        stage_number=1,
        difficulty="easy",
        letters=["a", "a", "e", "k", "l", "m", "r", "t"],
        min_length=3,
        duration_seconds=45,
        phase_started_at=datetime.now(timezone.utc),
        phase_ends_at=datetime.now(timezone.utc) + timedelta(seconds=45),
        remaining_seconds=45,
        own_words=[],
        own_word_count=0,
        players=[],
        latest_result=None,
        winner_user_id=None,
    )

    with patch(
        "app.api.routes.kelime_kapismasi.room_connections.broadcast",
        AsyncMock(),
    ) as broadcast:
        await _broadcast("JAM-TEST", game)

    payload = broadcast.await_args.args[1]
    assert payload == {
        "type": "kelime_kapismasi_updated",
        "room_code": "JAM-TEST",
        "game_id": str(game.id),
        "version": 8,
    }
    assert "words" not in payload
    assert "state" not in payload
    assert "letters" not in payload
