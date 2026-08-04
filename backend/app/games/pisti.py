from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

from app.games.cards import Card, fresh_deck


@dataclass(slots=True)
class PlayerState:
    user_id: str
    hand: list[Card] = field(default_factory=list)
    captured: list[Card] = field(default_factory=list)
    pisti_count: int = 0


@dataclass(slots=True)
class PistiState:
    players: list[PlayerState]
    deck: list[Card]
    table: list[Card]
    turn_index: int = 0
    last_capturer_index: int | None = None
    status: Literal["active", "finished"] = "active"


def start_game(
    user_ids: Sequence[str],
    *,
    rng: random.Random | None = None,
) -> PistiState:
    if len(user_ids) != 2:
        raise ValueError("Pişti MVP tam olarak iki oyuncu gerektirir.")
    if len(set(user_ids)) != len(user_ids):
        raise ValueError("Oyuncular benzersiz olmalıdır.")

    deck = fresh_deck(rng)
    players = [PlayerState(user_id=user_id) for user_id in user_ids]

    # Açılışta üç kapalı, bir açık olmak üzere dört kart masaya bırakılır.
    # Kartların tamamı oyun motorunda masada tutulur; kapalı/açık sunumu istemci yapar.
    table = [deck.pop() for _ in range(4)]
    state = PistiState(players=players, deck=deck, table=table)
    _deal_hands(state)
    return state


def play_card(state: PistiState, user_id: str, card_id: str) -> None:
    if state.status != "active":
        raise ValueError("Oyun tamamlandı.")

    player = state.players[state.turn_index]
    if player.user_id != user_id:
        raise ValueError("Hamle sırası bu oyuncuda değil.")

    card = next((candidate for candidate in player.hand if candidate.id == card_id), None)
    if card is None:
        raise ValueError("Kart oyuncunun elinde bulunamadı.")

    player.hand.remove(card)
    previous_top = state.table[-1] if state.table else None
    is_pisti = len(state.table) == 1 and previous_top is not None and card.rank == previous_top.rank
    captures = previous_top is not None and (card.rank == previous_top.rank or card.rank == "J")
    state.table.append(card)

    if captures:
        player.captured.extend(state.table)
        state.table.clear()
        state.last_capturer_index = state.turn_index
        if is_pisti:
            player.pisti_count += 1

    state.turn_index = (state.turn_index + 1) % len(state.players)

    if all(not candidate.hand for candidate in state.players):
        if state.deck:
            _deal_hands(state)
        else:
            _finish_game(state)


def scores(state: PistiState, *, include_majority: bool = True) -> dict[str, int]:
    """Return current scores.

    Special-card and Pişti points are visible during the game. The three-point
    card-majority bonus is added only after the round is finished.
    """
    result = {
        player.user_id: _captured_card_score(player) + player.pisti_count * 10
        for player in state.players
    }
    captured_counts = [len(player.captured) for player in state.players]
    if include_majority and captured_counts[0] != captured_counts[1]:
        result[state.players[captured_counts.index(max(captured_counts))].user_id] += 3
    return result


def _deal_hands(state: PistiState) -> None:
    for _ in range(4):
        for player in state.players:
            if state.deck:
                player.hand.append(state.deck.pop())


def _finish_game(state: PistiState) -> None:
    if state.table and state.last_capturer_index is not None:
        state.players[state.last_capturer_index].captured.extend(state.table)
        state.table.clear()
    state.status = "finished"


def _captured_card_score(player: PlayerState) -> int:
    score = 0
    for card in player.captured:
        if card.rank in {"A", "J"}:
            score += 1
        elif card.rank == "2" and card.suit == "clubs":
            score += 2
        elif card.rank == "10" and card.suit == "diamonds":
            score += 3
    return score
