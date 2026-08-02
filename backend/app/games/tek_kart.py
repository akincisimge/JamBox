from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

Color = Literal["red", "yellow", "green", "blue"]
CardKind = Literal[
    "number",
    "skip",
    "reverse",
    "draw_two",
    "wild",
    "wild_draw_four",
]
GameStatus = Literal["active", "finished"]

COLORS: tuple[Color, ...] = ("red", "yellow", "green", "blue")


@dataclass(frozen=True, slots=True)
class TekKartCard:
    id: str
    kind: CardKind
    color: Color | None = None
    number: int | None = None

    @property
    def symbol(self) -> str:
        if self.kind == "number":
            if self.number is None:
                raise ValueError("Sayı kartında sayı bulunmalıdır.")
            return str(self.number)
        return self.kind


@dataclass(slots=True)
class TekKartPlayerState:
    user_id: str
    hand: list[TekKartCard] = field(default_factory=list)
    called_tek_kart: bool = False


@dataclass(slots=True)
class TekKartState:
    players: list[TekKartPlayerState]
    draw_pile: list[TekKartCard]
    discard_pile: list[TekKartCard]
    active_color: Color
    turn_index: int = 0
    direction: Literal[-1, 1] = 1
    status: GameStatus = "active"
    winner_user_id: str | None = None
    log: list[str] = field(default_factory=list)


def fresh_deck(rng: random.Random | None = None) -> list[TekKartCard]:
    deck: list[TekKartCard] = []

    for color in COLORS:
        deck.append(TekKartCard(id=f"{color}-0-1", kind="number", color=color, number=0))
        for number in range(1, 10):
            for copy in (1, 2):
                deck.append(
                    TekKartCard(
                        id=f"{color}-{number}-{copy}",
                        kind="number",
                        color=color,
                        number=number,
                    )
                )
        for kind in ("skip", "reverse", "draw_two"):
            for copy in (1, 2):
                deck.append(
                    TekKartCard(
                        id=f"{color}-{kind}-{copy}",
                        kind=kind,
                        color=color,
                    )
                )

    for copy in range(1, 5):
        deck.append(TekKartCard(id=f"wild-{copy}", kind="wild"))
        deck.append(TekKartCard(id=f"wild-draw-four-{copy}", kind="wild_draw_four"))

    (rng or random.SystemRandom()).shuffle(deck)
    return deck


def start_game(
    user_ids: Sequence[str],
    *,
    rng: random.Random | None = None,
) -> TekKartState:
    if len(user_ids) < 2 or len(user_ids) > 4:
        raise ValueError("Tek Kart 2-4 oyuncu gerektirir.")
    if len(set(user_ids)) != len(user_ids):
        raise ValueError("Oyuncular benzersiz olmalıdır.")

    deck = fresh_deck(rng)
    players = [TekKartPlayerState(user_id=user_id) for user_id in user_ids]

    for _ in range(7):
        for player in players:
            player.hand.append(deck.pop())

    deferred: list[TekKartCard] = []
    starter: TekKartCard | None = None
    while deck:
        candidate = deck.pop()
        if candidate.kind == "number":
            starter = candidate
            break
        deferred.append(candidate)

    if starter is None or starter.color is None:
        raise RuntimeError("Başlangıç kartı oluşturulamadı.")

    deck.extend(deferred)
    return TekKartState(
        players=players,
        draw_pile=deck,
        discard_pile=[starter],
        active_color=starter.color,
    )


def playable_cards(state: TekKartState, user_id: str) -> list[TekKartCard]:
    player = _player_for_user(state, user_id)
    return [card for card in player.hand if _card_can_be_played(state, player, card)]


def call_tek_kart(state: TekKartState, user_id: str) -> None:
    _ensure_active(state)
    player = _current_player(state)
    if player.user_id != user_id:
        raise ValueError("Tek Kart çağrısı yalnızca sırası gelen oyuncu tarafından yapılabilir.")
    if len(player.hand) != 2:
        raise ValueError("Tek Kart çağrısı elde iki kart varken yapılabilir.")

    player.called_tek_kart = True
    state.log.append(f"{user_id} Tek Kart dedi.")


def play_card(
    state: TekKartState,
    user_id: str,
    card_id: str,
    *,
    chosen_color: Color | None = None,
) -> None:
    _ensure_active(state)
    player = _current_player(state)
    if player.user_id != user_id:
        raise ValueError("Hamle sırası bu oyuncuda değil.")

    card = next((candidate for candidate in player.hand if candidate.id == card_id), None)
    if card is None:
        raise ValueError("Kart oyuncunun elinde bulunamadı.")
    if not _card_can_be_played(state, player, card):
        raise ValueError("Bu kart mevcut kartın üzerine oynanamaz.")

    if card.kind in {"wild", "wild_draw_four"}:
        if chosen_color not in COLORS:
            raise ValueError("Renk seçen kart için geçerli bir renk seçilmelidir.")
    elif chosen_color is not None:
        raise ValueError("Bu kart oynanırken renk seçilemez.")

    player.hand.remove(card)
    state.discard_pile.append(card)
    if card.kind in {"wild", "wild_draw_four"}:
        state.active_color = chosen_color
    elif card.color is not None:
        state.active_color = card.color

    state.log.append(f"{user_id} {card.id} kartını oynadı.")

    if not player.hand:
        player.called_tek_kart = False
        state.status = "finished"
        state.winner_user_id = user_id
        state.log.append(f"{user_id} oyunu kazandı.")
        return

    if len(player.hand) == 1:
        if not player.called_tek_kart:
            penalty = _draw_cards(state, player, 2)
            state.log.append(f"{user_id} Tek Kart demedi ve {penalty} kart çekti.")
    player.called_tek_kart = False

    if card.kind == "skip":
        _advance_turn(state, 2)
        return

    if card.kind == "reverse":
        state.direction = -state.direction
        _advance_turn(state, 2 if len(state.players) == 2 else 1)
        return

    if card.kind == "draw_two":
        target = state.players[_next_index(state)]
        drawn = _draw_cards(state, target, 2)
        state.log.append(f"{target.user_id} {drawn} kart çekti.")
        _advance_turn(state, 2)
        return

    if card.kind == "wild_draw_four":
        target = state.players[_next_index(state)]
        drawn = _draw_cards(state, target, 4)
        state.log.append(f"{target.user_id} {drawn} kart çekti.")
        _advance_turn(state, 2)
        return

    _advance_turn(state)


def draw_card(state: TekKartState, user_id: str) -> TekKartCard:
    _ensure_active(state)
    player = _current_player(state)
    if player.user_id != user_id:
        raise ValueError("Hamle sırası bu oyuncuda değil.")
    if playable_cards(state, user_id):
        raise ValueError("Elde oynanabilir kart varken kart çekilemez.")

    cards = _take_from_draw_pile(state, 1)
    if not cards:
        raise ValueError("Çekilecek kart kalmadı.")

    card = cards[0]
    player.hand.append(card)
    player.called_tek_kart = False
    state.log.append(f"{user_id} bir kart çekti.")
    _advance_turn(state)
    return card


def _ensure_active(state: TekKartState) -> None:
    if state.status != "active":
        raise ValueError("Oyun aktif değil.")


def _current_player(state: TekKartState) -> TekKartPlayerState:
    return state.players[state.turn_index]


def _player_for_user(state: TekKartState, user_id: str) -> TekKartPlayerState:
    player = next((candidate for candidate in state.players if candidate.user_id == user_id), None)
    if player is None:
        raise ValueError("Oyuncu bu oyunda bulunamadı.")
    return player


def _card_can_be_played(
    state: TekKartState,
    player: TekKartPlayerState,
    card: TekKartCard,
) -> bool:
    if card.kind == "wild":
        return True
    if card.kind == "wild_draw_four":
        return not any(
            other.id != card.id and other.color == state.active_color for other in player.hand
        )
    if card.color == state.active_color:
        return True

    top_card = state.discard_pile[-1]
    return card.symbol == top_card.symbol


def _next_index(state: TekKartState, steps: int = 1) -> int:
    return (state.turn_index + state.direction * steps) % len(state.players)


def _advance_turn(state: TekKartState, steps: int = 1) -> None:
    state.turn_index = _next_index(state, steps)


def _draw_cards(
    state: TekKartState,
    player: TekKartPlayerState,
    count: int,
) -> int:
    cards = _take_from_draw_pile(state, count)
    player.hand.extend(cards)
    player.called_tek_kart = False
    return len(cards)


def _take_from_draw_pile(state: TekKartState, count: int) -> list[TekKartCard]:
    cards: list[TekKartCard] = []
    for _ in range(count):
        if not state.draw_pile:
            _refill_draw_pile(state)
        if not state.draw_pile:
            break
        cards.append(state.draw_pile.pop())
    return cards


def _refill_draw_pile(state: TekKartState) -> None:
    if len(state.discard_pile) <= 1:
        return

    top_card = state.discard_pile[-1]
    recycled = state.discard_pile[:-1]
    random.SystemRandom().shuffle(recycled)
    state.draw_pile.extend(recycled)
    state.discard_pile = [top_card]
