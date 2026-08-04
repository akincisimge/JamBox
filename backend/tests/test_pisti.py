import random

import pytest

from app.games.pisti import Card, PistiState, PlayerState, play_card, scores, start_game


def test_start_game_creates_complete_two_player_deal() -> None:
    state = start_game(["simge", "friend"], rng=random.Random(42))

    assert len(state.table) == 4
    assert [len(player.hand) for player in state.players] == [4, 4]
    assert len(state.deck) == 40
    all_cards = state.table + state.deck + state.players[0].hand + state.players[1].hand
    assert len(all_cards) == 52
    assert len({card.id for card in all_cards}) == 52


def test_matching_rank_captures_table_and_counts_single_card_pisti() -> None:
    matching = Card("hearts", "7")
    state = PistiState(
        players=[
            PlayerState("simge", hand=[Card("spades", "7")]),
            PlayerState("friend", hand=[Card("clubs", "3")]),
        ],
        deck=[],
        table=[matching],
    )

    play_card(state, "simge", "7-spades")

    assert state.table == []
    assert len(state.players[0].captured) == 2
    assert state.players[0].pisti_count == 1


def test_jack_captures_without_pisti_when_rank_does_not_match() -> None:
    state = PistiState(
        players=[
            PlayerState("simge", hand=[Card("spades", "J")]),
            PlayerState("friend", hand=[Card("clubs", "3")]),
        ],
        deck=[],
        table=[Card("hearts", "7")],
    )

    play_card(state, "simge", "J-spades")

    assert len(state.players[0].captured) == 2
    assert state.players[0].pisti_count == 0


def test_player_cannot_play_out_of_turn_or_use_unknown_card() -> None:
    state = PistiState(
        players=[
            PlayerState("simge", hand=[Card("spades", "A")]),
            PlayerState("friend", hand=[Card("clubs", "3")]),
        ],
        deck=[],
        table=[],
    )

    with pytest.raises(ValueError, match="Hamle sırası"):
        play_card(state, "friend", "3-clubs")

    with pytest.raises(ValueError, match="elinde bulunamadı"):
        play_card(state, "simge", "K-hearts")


def test_scoring_includes_special_cards_pisti_and_card_majority() -> None:
    state = PistiState(
        players=[
            PlayerState(
                "simge",
                captured=[
                    Card("spades", "A"),
                    Card("hearts", "J"),
                    Card("clubs", "2"),
                    Card("diamonds", "10"),
                    Card("clubs", "4"),
                ],
                pisti_count=1,
            ),
            PlayerState("friend", captured=[Card("hearts", "4")]),
        ],
        deck=[],
        table=[],
        status="finished",
    )

    assert scores(state) == {"simge": 20, "friend": 0}


def test_running_score_does_not_award_card_majority_early() -> None:
    state = PistiState(
        players=[
            PlayerState(
                "simge",
                captured=[Card("spades", "A"), Card("clubs", "4")],
                pisti_count=1,
            ),
            PlayerState("friend", captured=[]),
        ],
        deck=[Card("hearts", "5")],
        table=[],
    )

    assert scores(state, include_majority=False) == {"simge": 11, "friend": 0}
    assert scores(state) == {"simge": 14, "friend": 0}
