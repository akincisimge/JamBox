import random
from collections import Counter

import pytest

from app.games.tek_kart import (
    TekKartCard,
    TekKartPlayerState,
    TekKartState,
    call_tek_kart,
    draw_card,
    fresh_deck,
    play_card,
    playable_cards,
    start_game,
)


def card(
    card_id: str,
    *,
    kind: str = "number",
    color: str | None = None,
    number: int | None = None,
) -> TekKartCard:
    return TekKartCard(id=card_id, kind=kind, color=color, number=number)


def make_state(
    *hands: list[TekKartCard],
    top: TekKartCard,
    active_color: str,
    draw_pile: list[TekKartCard] | None = None,
) -> TekKartState:
    players = [
        TekKartPlayerState(user_id=f"user-{index + 1}", hand=list(hand))
        for index, hand in enumerate(hands)
    ]
    return TekKartState(
        players=players,
        draw_pile=list(draw_pile or []),
        discard_pile=[top],
        active_color=active_color,
    )


def test_fresh_deck_has_expected_composition_and_unique_ids() -> None:
    deck = fresh_deck(random.Random(3))

    assert len(deck) == 108
    assert len({item.id for item in deck}) == 108
    assert Counter(item.kind for item in deck) == {
        "number": 76,
        "skip": 8,
        "reverse": 8,
        "draw_two": 8,
        "wild": 4,
        "wild_draw_four": 4,
    }


def test_start_game_deals_seven_cards_and_uses_number_starter() -> None:
    state = start_game(["a", "b", "c"], rng=random.Random(7))

    assert [len(player.hand) for player in state.players] == [7, 7, 7]
    assert len(state.draw_pile) == 86
    assert state.discard_pile[-1].kind == "number"
    assert state.active_color == state.discard_pile[-1].color
    assert state.turn_index == 0
    assert state.direction == 1


@pytest.mark.parametrize("user_ids", [[], ["a"], ["a", "b", "c", "d", "e"]])
def test_start_game_requires_two_to_four_players(user_ids: list[str]) -> None:
    with pytest.raises(ValueError, match="2-4"):
        start_game(user_ids)


def test_start_game_rejects_duplicate_players() -> None:
    with pytest.raises(ValueError, match="benzersiz"):
        start_game(["a", "a"])


def test_play_card_accepts_matching_color_and_advances_turn() -> None:
    red_three = card("red-3", color="red", number=3)
    state = make_state(
        [red_three, card("blue-8", color="blue", number=8)],
        [card("yellow-1", color="yellow", number=1)],
        top=card("red-5", color="red", number=5),
        active_color="red",
    )

    play_card(state, "user-1", red_three.id)

    assert state.discard_pile[-1] == red_three
    assert state.active_color == "red"
    assert state.turn_index == 1


def test_play_card_accepts_matching_symbol() -> None:
    blue_five = card("blue-5", color="blue", number=5)
    state = make_state(
        [blue_five, card("green-8", color="green", number=8)],
        [card("yellow-1", color="yellow", number=1)],
        top=card("red-5", color="red", number=5),
        active_color="red",
    )

    play_card(state, "user-1", blue_five.id)

    assert state.active_color == "blue"
    assert state.turn_index == 1


def test_play_card_rejects_wrong_turn_and_unplayable_card() -> None:
    blue_three = card("blue-3", color="blue", number=3)
    state = make_state(
        [blue_three, card("green-8", color="green", number=8)],
        [card("yellow-1", color="yellow", number=1)],
        top=card("red-5", color="red", number=5),
        active_color="red",
    )

    with pytest.raises(ValueError, match="Hamle sırası"):
        play_card(state, "user-2", "yellow-1")
    with pytest.raises(ValueError, match="oynanamaz"):
        play_card(state, "user-1", blue_three.id)


def test_skip_skips_next_player() -> None:
    skip = card("red-skip", kind="skip", color="red")
    state = make_state(
        [skip, card("blue-8", color="blue", number=8)],
        [card("yellow-1", color="yellow", number=1)],
        [card("green-2", color="green", number=2)],
        top=card("red-5", color="red", number=5),
        active_color="red",
    )

    play_card(state, "user-1", skip.id)

    assert state.turn_index == 2


def test_reverse_changes_direction_for_three_players() -> None:
    reverse = card("red-reverse", kind="reverse", color="red")
    state = make_state(
        [reverse, card("blue-8", color="blue", number=8)],
        [card("yellow-1", color="yellow", number=1)],
        [card("green-2", color="green", number=2)],
        top=card("red-5", color="red", number=5),
        active_color="red",
    )

    play_card(state, "user-1", reverse.id)

    assert state.direction == -1
    assert state.turn_index == 2


def test_reverse_acts_as_skip_with_two_players() -> None:
    reverse = card("red-reverse", kind="reverse", color="red")
    state = make_state(
        [reverse, card("blue-8", color="blue", number=8)],
        [card("yellow-1", color="yellow", number=1)],
        top=card("red-5", color="red", number=5),
        active_color="red",
    )

    play_card(state, "user-1", reverse.id)

    assert state.direction == -1
    assert state.turn_index == 0


def test_draw_two_penalizes_and_skips_next_player() -> None:
    draw_two = card("red-draw-two", kind="draw_two", color="red")
    penalty_cards = [
        card("green-1", color="green", number=1),
        card("yellow-2", color="yellow", number=2),
    ]
    state = make_state(
        [draw_two, card("blue-8", color="blue", number=8)],
        [card("yellow-1", color="yellow", number=1)],
        [card("green-2", color="green", number=2)],
        top=card("red-5", color="red", number=5),
        active_color="red",
        draw_pile=penalty_cards,
    )

    call_tek_kart(state, "user-1")
    play_card(state, "user-1", draw_two.id)

    assert len(state.players[1].hand) == 3
    assert state.turn_index == 2


def test_wild_requires_and_applies_chosen_color() -> None:
    wild = card("wild", kind="wild")
    state = make_state(
        [wild, card("blue-8", color="blue", number=8)],
        [card("yellow-1", color="yellow", number=1)],
        top=card("red-5", color="red", number=5),
        active_color="red",
    )

    with pytest.raises(ValueError, match="renk seçilmelidir"):
        play_card(state, "user-1", wild.id)

    play_card(state, "user-1", wild.id, chosen_color="green")

    assert state.active_color == "green"


def test_wild_draw_four_is_blocked_when_player_has_matching_color() -> None:
    wild_draw_four = card("wild-draw-four", kind="wild_draw_four")
    red_two = card("red-2", color="red", number=2)
    state = make_state(
        [wild_draw_four, red_two],
        [card("yellow-1", color="yellow", number=1)],
        top=card("red-5", color="red", number=5),
        active_color="red",
    )

    assert wild_draw_four not in playable_cards(state, "user-1")
    with pytest.raises(ValueError, match="oynanamaz"):
        play_card(state, "user-1", wild_draw_four.id, chosen_color="blue")


def test_wild_draw_four_draws_four_and_skips_target() -> None:
    wild_draw_four = card("wild-draw-four", kind="wild_draw_four")
    draw_pile = [
        card(f"green-{number}", color="green", number=number) for number in range(1, 5)
    ]
    state = make_state(
        [wild_draw_four, card("blue-8", color="blue", number=8)],
        [card("yellow-1", color="yellow", number=1)],
        [card("green-8", color="green", number=8)],
        top=card("red-5", color="red", number=5),
        active_color="red",
        draw_pile=draw_pile,
    )

    call_tek_kart(state, "user-1")
    play_card(state, "user-1", wild_draw_four.id, chosen_color="yellow")

    assert len(state.players[1].hand) == 5
    assert state.active_color == "yellow"
    assert state.turn_index == 2


def test_draw_card_is_only_allowed_without_playable_card_and_ends_turn() -> None:
    state = make_state(
        [card("red-3", color="red", number=3)],
        [card("yellow-1", color="yellow", number=1)],
        top=card("blue-5", color="blue", number=5),
        active_color="blue",
        draw_pile=[card("green-8", color="green", number=8)],
    )

    drawn = draw_card(state, "user-1")

    assert drawn.id == "green-8"
    assert len(state.players[0].hand) == 2
    assert state.turn_index == 1


def test_draw_card_is_rejected_when_player_can_play() -> None:
    state = make_state(
        [card("blue-3", color="blue", number=3)],
        [card("yellow-1", color="yellow", number=1)],
        top=card("blue-5", color="blue", number=5),
        active_color="blue",
        draw_pile=[card("green-8", color="green", number=8)],
    )

    with pytest.raises(ValueError, match="oynanabilir"):
        draw_card(state, "user-1")


def test_missing_tek_kart_call_applies_two_card_penalty() -> None:
    red_two = card("red-2", color="red", number=2)
    state = make_state(
        [red_two, card("blue-8", color="blue", number=8)],
        [card("yellow-1", color="yellow", number=1)],
        top=card("red-5", color="red", number=5),
        active_color="red",
        draw_pile=[
            card("green-1", color="green", number=1),
            card("yellow-2", color="yellow", number=2),
        ],
    )

    play_card(state, "user-1", red_two.id)

    assert len(state.players[0].hand) == 3


def test_tek_kart_call_avoids_penalty() -> None:
    red_two = card("red-2", color="red", number=2)
    state = make_state(
        [red_two, card("blue-8", color="blue", number=8)],
        [card("yellow-1", color="yellow", number=1)],
        top=card("red-5", color="red", number=5),
        active_color="red",
        draw_pile=[
            card("green-1", color="green", number=1),
            card("yellow-2", color="yellow", number=2),
        ],
    )

    call_tek_kart(state, "user-1")
    play_card(state, "user-1", red_two.id)

    assert len(state.players[0].hand) == 1
    assert state.turn_index == 1


def test_call_tek_kart_requires_current_player_with_two_cards() -> None:
    state = make_state(
        [card("red-2", color="red", number=2)],
        [card("yellow-1", color="yellow", number=1)],
        top=card("red-5", color="red", number=5),
        active_color="red",
    )

    with pytest.raises(ValueError, match="iki kart"):
        call_tek_kart(state, "user-1")
    with pytest.raises(ValueError, match="sırası gelen"):
        call_tek_kart(state, "user-2")


def test_playing_last_card_finishes_game() -> None:
    red_two = card("red-2", color="red", number=2)
    state = make_state(
        [red_two],
        [card("yellow-1", color="yellow", number=1)],
        top=card("red-5", color="red", number=5),
        active_color="red",
    )

    play_card(state, "user-1", red_two.id)

    assert state.status == "finished"
    assert state.winner_user_id == "user-1"
    assert not state.players[0].hand


def test_draw_pile_is_rebuilt_from_discard_pile() -> None:
    top = card("blue-5", color="blue", number=5)
    recycled = card("green-8", color="green", number=8)
    state = make_state(
        [card("red-3", color="red", number=3)],
        [card("yellow-1", color="yellow", number=1)],
        top=top,
        active_color="blue",
    )
    state.discard_pile = [recycled, top]

    drawn = draw_card(state, "user-1")

    assert drawn == recycled
    assert state.discard_pile == [top]
