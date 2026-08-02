from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal, Sequence

from app.games.cards import Card, fresh_deck

@dataclass(slots=True)
class PapazKactiPlayerState:
    user_id: str
    hand: list[Card] = field(default_factory=list)
    is_finished: bool = False

@dataclass(slots=True)
class PapazKactiState:
    players: list[PapazKactiPlayerState]
    turn_index: int = 0
    status: Literal["waiting", "active", "finished"] = "active"
    loser_user_id: str | None = None
    log: list[str] = field(default_factory=list)


def start_game(
    user_ids: Sequence[str],
    *,
    rng: random.Random | None = None,
) -> PapazKactiState:
    if len(user_ids) < 2 or len(user_ids) > 4:
        raise ValueError("Papaz Kaçtı 2-4 oyuncu gerektirir.")
    if len(set(user_ids)) != len(user_ids):
        raise ValueError("Oyuncular benzersiz olmalıdır.")

    deck = fresh_deck(rng)
    
    # Remove one King (e.g., King of Clubs) to leave 3 Kings. 
    # Two of them will form a pair, leaving exactly 1 unique King.
    king_of_clubs = Card(suit="clubs", rank="K")
    deck.remove(king_of_clubs)

    players = [PapazKactiPlayerState(user_id=user_id) for user_id in user_ids]
    
    # Deal cards
    current_player_idx = 0
    while deck:
        players[current_player_idx].hand.append(deck.pop())
        current_player_idx = (current_player_idx + 1) % len(players)
    
    # Automatically discard pairs
    for player in players:
        _discard_pairs(player)
        if not player.hand:
            player.is_finished = True
            
    state = PapazKactiState(players=players)
    
    # Fast forward turn if first player finished on deal
    _advance_turn_if_needed(state)
    
    return state


def draw_card(state: PapazKactiState, user_id: str, card_index: int, rng: random.Random | None = None) -> None:
    if state.status != "active":
        raise ValueError("Oyun aktif değil.")
        
    current_player = state.players[state.turn_index]
    if current_player.user_id != user_id:
        raise ValueError("Hamle sırası bu oyuncuda değil.")
        
    target_player = _get_next_active_player(state, state.turn_index)
    if not target_player:
        raise ValueError("Oyun zaten bitmiş.")
        
    if card_index < 0 or card_index >= len(target_player.hand):
        raise ValueError("Geçersiz kart indeksi.")
        
    # Draw the card
    drawn_card = target_player.hand.pop(card_index)
    current_player.hand.append(drawn_card)
    
    state.log.append(f"{current_player.user_id} drew a card.")
    
    # Check if target player finished
    if not target_player.hand:
        target_player.is_finished = True
        state.log.append(f"{target_player.user_id} finished.")
        
    # Discard pairs for current player
    _discard_pairs(current_player)
    
    # Check if current player finished
    if not current_player.hand:
        current_player.is_finished = True
        state.log.append(f"{current_player.user_id} finished.")
        
    # Advance turn to the next active player
    _advance_turn(state)


def _discard_pairs(player: PapazKactiPlayerState) -> None:
    """Removes pairs of same rank from player's hand."""
    new_hand: list[Card] = []
    # Count occurrences
    rank_counts: dict[str, int] = {}
    for card in player.hand:
        rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        
    # Keep only odd occurrences (1 card if 1 or 3, 0 if 2 or 4)
    ranks_to_keep: dict[str, int] = {r: count % 2 for r, count in rank_counts.items()}
    
    for card in player.hand:
        if ranks_to_keep[card.rank] > 0:
            new_hand.append(card)
            ranks_to_keep[card.rank] -= 1
            
    player.hand = new_hand


def _get_next_active_player(state: PapazKactiState, current_index: int) -> PapazKactiPlayerState | None:
    n = len(state.players)
    for i in range(1, n):
        idx = (current_index + i) % n
        if not state.players[idx].is_finished:
            return state.players[idx]
    return None


def _advance_turn(state: PapazKactiState) -> None:
    active_players = [p for p in state.players if not p.is_finished]
    
    if len(active_players) <= 1:
        state.status = "finished"
        if len(active_players) == 1:
            state.loser_user_id = active_players[0].user_id
        return
        
    next_player = _get_next_active_player(state, state.turn_index)
    if next_player:
        state.turn_index = state.players.index(next_player)


def _advance_turn_if_needed(state: PapazKactiState) -> None:
    active_players = [p for p in state.players if not p.is_finished]
    if len(active_players) <= 1:
        state.status = "finished"
        if len(active_players) == 1:
            state.loser_user_id = active_players[0].user_id
        return
        
    if state.players[state.turn_index].is_finished:
        _advance_turn(state)
