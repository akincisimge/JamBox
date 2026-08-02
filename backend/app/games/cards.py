import random
from dataclasses import dataclass
from typing import Literal

Suit = Literal["clubs", "diamonds", "hearts", "spades"]
Rank = Literal["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

SUITS: tuple[Suit, ...] = ("clubs", "diamonds", "hearts", "spades")
RANKS: tuple[Rank, ...] = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")


@dataclass(frozen=True, slots=True)
class Card:
    suit: Suit
    rank: Rank

    @property
    def id(self) -> str:
        return f"{self.rank}-{self.suit}"


def fresh_deck(rng: random.Random | None = None) -> list[Card]:
    deck = [Card(suit=suit, rank=rank) for suit in SUITS for rank in RANKS]
    (rng or random.SystemRandom()).shuffle(deck)
    return deck
