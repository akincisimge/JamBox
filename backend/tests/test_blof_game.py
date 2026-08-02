import random

import pytest

from app.games.blof import (
    BlofPlayerState,
    BlofState,
    accept_last_play,
    call_bluff,
    play_cards,
    start_game,
)
from app.games.cards import Card


def test_deal_is_balanced_for_two_to_four_players() -> None:
    for player_count in (2, 3, 4):
        state = start_game(
            [f"player-{index}" for index in range(player_count)],
            rng=random.Random(42),
        )
        counts = [len(player.hand) for player in state.players]
        assert sum(counts) == 52
        assert max(counts) - min(counts) <= 1


def test_start_requires_two_to_four_unique_players() -> None:
    with pytest.raises(ValueError, match="2-4"):
        start_game(["one"])
    with pytest.raises(ValueError, match="2-4"):
        start_game(["1", "2", "3", "4", "5"])
    with pytest.raises(ValueError, match="benzersiz"):
        start_game(["same", "same"])


def test_play_removes_cards_and_advances_turn() -> None:
    state = BlofState(
        players=[
            BlofPlayerState("one", [Card("clubs", "2"), Card("spades", "5")]),
            BlofPlayerState("two", [Card("hearts", "A")]),
        ]
    )
    play_cards(state, "one", ["2-clubs"], "K")
    assert [card.id for card in state.players[0].hand] == ["5-spades"]
    assert state.turn_index == 1
    assert state.last_declared_rank == "K"
    assert len(state.pile) == 1


def test_invalid_card_and_duplicate_card_are_rejected() -> None:
    state = BlofState(
        players=[
            BlofPlayerState("one", [Card("clubs", "2")]),
            BlofPlayerState("two", [Card("hearts", "A")]),
        ]
    )
    with pytest.raises(ValueError, match="elinizde değil"):
        play_cards(state, "one", ["K-spades"], "K")
    with pytest.raises(ValueError, match="iki kez"):
        play_cards(state, "one", ["2-clubs", "2-clubs"], "2")


def test_wrong_turn_is_rejected() -> None:
    state = BlofState(
        players=[
            BlofPlayerState("one", [Card("clubs", "2")]),
            BlofPlayerState("two", [Card("hearts", "A")]),
        ]
    )
    with pytest.raises(ValueError, match="Hamle sırası"):
        play_cards(state, "two", ["A-hearts"], "A")


def test_false_declaration_makes_player_take_pile() -> None:
    state = BlofState(
        players=[
            BlofPlayerState("one", [Card("clubs", "2"), Card("spades", "5")]),
            BlofPlayerState("two", [Card("hearts", "A")]),
        ]
    )
    play_cards(state, "one", ["2-clubs"], "K")
    result = call_bluff(state, "two")
    assert result.truthful is False
    assert result.pile_receiver_user_id == "one"
    assert len(state.players[0].hand) == 2
    assert state.turn_index == 1
    assert state.pile == []


def test_true_declaration_makes_challenger_take_pile() -> None:
    state = BlofState(
        players=[
            BlofPlayerState("one", [Card("clubs", "2"), Card("spades", "5")]),
            BlofPlayerState("two", [Card("hearts", "A")]),
        ]
    )
    play_cards(state, "one", ["2-clubs"], "2")
    result = call_bluff(state, "two")
    assert result.truthful is True
    assert result.pile_receiver_user_id == "two"
    assert len(state.players[1].hand) == 2
    assert state.turn_index == 0


def test_pending_winner_is_not_finished_until_resolved() -> None:
    state = BlofState(
        players=[
            BlofPlayerState("one", [Card("clubs", "2")]),
            BlofPlayerState("two", [Card("hearts", "A")]),
        ]
    )
    play_cards(state, "one", ["2-clubs"], "K")
    assert state.status == "active"
    assert state.pending_winner_user_id == "one"

    call_bluff(state, "two")
    assert state.status == "active"
    assert state.winner_user_id is None
    assert len(state.players[0].hand) == 1


def test_truthful_pending_winner_wins_after_challenge() -> None:
    state = BlofState(
        players=[
            BlofPlayerState("one", [Card("clubs", "2")]),
            BlofPlayerState("two", [Card("hearts", "A")]),
        ]
    )
    play_cards(state, "one", ["2-clubs"], "2")
    call_bluff(state, "two")
    assert state.status == "finished"
    assert state.winner_user_id == "one"


def test_accept_finishes_pending_winner() -> None:
    state = BlofState(
        players=[
            BlofPlayerState("one", [Card("clubs", "2")]),
            BlofPlayerState("two", [Card("hearts", "A")]),
        ]
    )
    play_cards(state, "one", ["2-clubs"], "K")
    accept_last_play(state, "two")
    assert state.status == "finished"
    assert state.winner_user_id == "one"


def test_finished_game_rejects_moves() -> None:
    state = BlofState(
        players=[
            BlofPlayerState("one", [Card("clubs", "2")]),
            BlofPlayerState("two", [Card("hearts", "A")]),
        ],
        status="finished",
    )
    with pytest.raises(ValueError, match="aktif değil"):
        play_cards(state, "one", ["2-clubs"], "2")
