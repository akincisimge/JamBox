from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

from app.games.cards import Card, Rank, fresh_deck

BlofStatus = Literal["waiting", "active", "finished"]


@dataclass(slots=True)
class BlofPlayerState:
    user_id: str
    hand: list[Card] = field(default_factory=list)


@dataclass(slots=True)
class BlofChallengeResult:
    truthful: bool
    challenger_user_id: str
    challenged_user_id: str
    pile_receiver_user_id: str
    next_turn_user_id: str | None
    revealed_cards: list[Card] = field(default_factory=list)


@dataclass(slots=True)
class BlofState:
    players: list[BlofPlayerState]
    turn_index: int = 0
    status: BlofStatus = "active"
    pile: list[Card] = field(default_factory=list)
    last_played_cards: list[Card] = field(default_factory=list)
    last_declared_rank: Rank | None = None
    last_player_user_id: str | None = None
    pending_winner_user_id: str | None = None
    winner_user_id: str | None = None
    last_result: BlofChallengeResult | None = None


def start_game(
    user_ids: Sequence[str],
    *,
    rng: random.Random | None = None,
) -> BlofState:
    if not 2 <= len(user_ids) <= 4:
        raise ValueError("Blöf 2-4 oyuncu gerektirir.")
    if len(set(user_ids)) != len(user_ids):
        raise ValueError("Oyuncular benzersiz olmalıdır.")

    players = [BlofPlayerState(user_id=user_id) for user_id in user_ids]
    for index, card in enumerate(fresh_deck(rng)):
        players[index % len(players)].hand.append(card)

    return BlofState(players=players)


def play_cards(
    state: BlofState,
    user_id: str,
    card_ids: Sequence[str],
    declared_rank: Rank,
) -> None:
    _require_active_turn(state, user_id)
    if state.pending_winner_user_id is not None:
        raise ValueError("Son hamle önce kabul edilmeli veya Blöf denmelidir.")
    if declared_rank not in {
        "A",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "J",
        "Q",
        "K",
    }:
        raise ValueError("Geçersiz kart değeri ilanı.")
    if not card_ids:
        raise ValueError("En az bir kart oynamalısınız.")
    if len(set(card_ids)) != len(card_ids):
        raise ValueError("Aynı kart iki kez oynanamaz.")

    player = state.players[state.turn_index]
    hand_by_id = {card.id: card for card in player.hand}
    if any(card_id not in hand_by_id for card_id in card_ids):
        raise ValueError("Seçilen kartlardan biri elinizde değil.")

    played_cards = [hand_by_id[card_id] for card_id in card_ids]
    selected_ids = set(card_ids)
    player.hand = [card for card in player.hand if card.id not in selected_ids]
    state.pile.extend(played_cards)
    state.last_played_cards = played_cards
    state.last_declared_rank = declared_rank
    state.last_player_user_id = user_id
    state.last_result = None
    state.pending_winner_user_id = user_id if not player.hand else None
    state.turn_index = _next_player_index(state, state.turn_index)


def call_bluff(state: BlofState, user_id: str) -> BlofChallengeResult:
    _require_active_turn(state, user_id)
    if not state.last_played_cards or state.last_declared_rank is None:
        raise ValueError("İtiraz edilebilecek bir son hamle yok.")
    if state.last_player_user_id is None or state.last_player_user_id == user_id:
        raise ValueError("Kendi hamlenize Blöf diyemezsiniz.")

    challenged_user_id = state.last_player_user_id
    truthful = all(
        card.rank == state.last_declared_rank for card in state.last_played_cards
    )
    pile_receiver_user_id = user_id if truthful else challenged_user_id
    challenge_winner_user_id = challenged_user_id if truthful else user_id

    receiver = _player_by_id(state, pile_receiver_user_id)
    receiver.hand.extend(state.pile)

    revealed_cards = list(state.last_played_cards)
    pending_winner_user_id = state.pending_winner_user_id
    next_turn_user_id: str | None = challenge_winner_user_id

    state.pile = []
    state.last_played_cards = []
    state.last_declared_rank = None
    state.last_player_user_id = None
    state.pending_winner_user_id = None

    if truthful and pending_winner_user_id == challenged_user_id:
        state.status = "finished"
        state.winner_user_id = challenged_user_id
        next_turn_user_id = None
    else:
        state.turn_index = _player_index(state, challenge_winner_user_id)

    result = BlofChallengeResult(
        truthful=truthful,
        challenger_user_id=user_id,
        challenged_user_id=challenged_user_id,
        pile_receiver_user_id=pile_receiver_user_id,
        next_turn_user_id=next_turn_user_id,
        revealed_cards=revealed_cards,
    )
    state.last_result = result
    return result


def accept_last_play(state: BlofState, user_id: str) -> None:
    _require_active_turn(state, user_id)
    if state.pending_winner_user_id is None:
        raise ValueError("Kabul edilmesi gereken bekleyen bir kazanan yok.")
    if not state.last_played_cards:
        raise ValueError("Kabul edilebilecek bir son hamle yok.")

    state.status = "finished"
    state.winner_user_id = state.pending_winner_user_id
    state.pending_winner_user_id = None
    state.last_result = None


def _require_active_turn(state: BlofState, user_id: str) -> None:
    if state.status != "active":
        raise ValueError("Oyun aktif değil.")
    if not state.players:
        raise ValueError("Oyuncu bulunamadı.")
    if state.players[state.turn_index].user_id != user_id:
        raise ValueError("Hamle sırası bu oyuncuda değil.")


def _next_player_index(state: BlofState, current_index: int) -> int:
    return (current_index + 1) % len(state.players)


def _player_index(state: BlofState, user_id: str) -> int:
    for index, player in enumerate(state.players):
        if player.user_id == user_id:
            return index
    raise ValueError("Oyuncu bulunamadı.")


def _player_by_id(state: BlofState, user_id: str) -> BlofPlayerState:
    return state.players[_player_index(state, user_id)]
