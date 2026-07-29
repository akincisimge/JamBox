import re
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import chess
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.room import ChessGame
from app.schemas.room import ChessMoveCreate, PlaybackUpdate
from app.services.errors import ConflictError, ForbiddenError
from app.services.rooms import (
    generate_room_code,
    get_room,
    join_chess_game,
    make_chess_move,
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
    assert "/api/rooms/{code}/messages" in schema["paths"]
    assert "/api/rooms/{code}/chess" in schema["paths"]
    assert "/api/rooms/{code}/chess/join" in schema["paths"]
    assert "/api/rooms/{code}/chess/moves" in schema["paths"]
    assert "/api/rooms/{code}/chess/restart" in schema["paths"]
    assert "/api/rooms/{code}/chess/resign" in schema["paths"]
    assert "/api/rooms/{code}/chess/draw" in schema["paths"]


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


def test_chess_game_rebuilds_legal_moves_and_san_history() -> None:
    board = chess.Board()
    first = chess.Move.from_uci("e2e4")
    board.push(first)
    second = chess.Move.from_uci("e7e5")
    board.push(second)
    game = ChessGame(
        status="active",
        fen=board.fen(),
        move_history=[first.uci(), second.uci()],
    )

    assert "g1f3" in game.legal_moves
    assert game.move_labels == ["e4", "e5"]


@pytest.mark.asyncio
async def test_second_room_member_can_accept_chess_invite() -> None:
    creator_id = uuid.uuid4()
    participant_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4(), code="JAM-CHESS1")
    participant = SimpleNamespace(id=participant_id)
    membership = SimpleNamespace(user_id=participant_id)
    game = SimpleNamespace(
        status="waiting",
        white_user_id=creator_id,
        black_user_id=None,
    )
    refreshed_room = SimpleNamespace(chess_game=game)
    session = AsyncMock()
    session.get.return_value = membership
    session.scalar.side_effect = [game, refreshed_room]

    result = await join_chess_game(session, room, participant)

    assert result is refreshed_room
    assert game.black_user_id == participant_id
    assert game.status == "active"
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_creator_cannot_accept_own_chess_invite() -> None:
    creator_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    creator = SimpleNamespace(id=creator_id)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=creator_id)
    session.scalar.return_value = SimpleNamespace(
        status="waiting",
        white_user_id=creator_id,
    )

    with pytest.raises(ConflictError, match="Kendi satranç davetinize"):
        await join_chess_game(session, room, creator)

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_chess_move_persists_fen_turn_and_history() -> None:
    white_id = uuid.uuid4()
    black_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4(), code="JAM-CHESS2")
    white = SimpleNamespace(id=white_id)
    membership = SimpleNamespace(user_id=white_id)
    opponent = SimpleNamespace(id=black_id, spotify_id="real-spotify-user")
    game = SimpleNamespace(
        status="active",
        white_user_id=white_id,
        black_user_id=black_id,
        fen=chess.STARTING_FEN,
        turn="white",
        move_history=[],
        draw_offer_user_id=black_id,
        winner_user_id=None,
        result=None,
    )
    refreshed_room = SimpleNamespace(chess_game=game)
    session = AsyncMock()
    session.get.side_effect = [membership, opponent]
    session.scalar.side_effect = [game, refreshed_room]

    result = await make_chess_move(
        session,
        room,
        white,
        ChessMoveCreate(from_square="e2", to_square="e4"),
    )

    assert result is refreshed_room
    assert game.move_history == ["e2e4"]
    assert game.turn == "black"
    assert game.draw_offer_user_id is None
    assert chess.Board(game.fen).piece_at(chess.E4) == chess.Piece(chess.PAWN, chess.WHITE)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_chess_rejects_move_when_it_is_not_players_turn() -> None:
    white_id = uuid.uuid4()
    black_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4())
    black = SimpleNamespace(id=black_id)
    session = AsyncMock()
    session.get.return_value = SimpleNamespace(user_id=black_id)
    session.scalar.return_value = SimpleNamespace(
        status="active",
        white_user_id=white_id,
        black_user_id=black_id,
        fen=chess.STARTING_FEN,
    )

    with pytest.raises(ConflictError, match="Hamle sırası sizde değil"):
        await make_chess_move(
            session,
            room,
            black,
            ChessMoveCreate(from_square="e7", to_square="e5"),
        )

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_jambot_answers_valid_player_move_in_same_transaction() -> None:
    white_id = uuid.uuid4()
    bot_id = uuid.uuid4()
    room = SimpleNamespace(id=uuid.uuid4(), code="JAM-BOT123")
    white = SimpleNamespace(id=white_id)
    membership = SimpleNamespace(user_id=white_id)
    bot = SimpleNamespace(
        id=bot_id,
        spotify_id=f"jambox-test-opponent-{room.id}",
    )
    game = SimpleNamespace(
        status="active",
        white_user_id=white_id,
        black_user_id=bot_id,
        fen=chess.STARTING_FEN,
        turn="white",
        move_history=[],
        draw_offer_user_id=None,
        winner_user_id=None,
        result=None,
    )
    refreshed_room = SimpleNamespace(chess_game=game)
    session = AsyncMock()
    session.get.side_effect = [membership, bot]
    session.scalar.side_effect = [game, refreshed_room]

    with patch("app.services.rooms.secrets.choice", side_effect=lambda moves: moves[0]):
        await make_chess_move(
            session,
            room,
            white,
            ChessMoveCreate(from_square="e2", to_square="e4"),
        )

    assert len(game.move_history) == 2
    assert game.move_history[0] == "e2e4"
    assert game.turn == "white"
    session.commit.assert_awaited_once()
