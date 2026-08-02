import random

from app.games.papaz_kacti import (
    draw_card,
    start_game,
)


def test_start_game():
    # 2 players
    user_ids = ["u1", "u2"]
    state = start_game(user_ids, rng=random.Random(42))
    
    assert state.status == "active"
    assert len(state.players) == 2
    
    # 51 cards total. Deal: 26 to u1, 25 to u2
    # But after auto-discard, hand sizes will be much smaller.
    assert len(state.players[0].hand) < 26
    assert len(state.players[1].hand) < 25
    
    # Ensure there are no pairs left in any hand
    for player in state.players:
        ranks = [card.rank for card in player.hand]
        assert len(ranks) == len(set(ranks))


def test_draw_card():
    user_ids = ["u1", "u2"]
    state = start_game(user_ids, rng=random.Random(42))
    
    p1 = state.players[0]
    p2 = state.players[1]
    
    p2_initial_hand_size = len(p2.hand)
    
    # Turn is 0 (u1)
    # Draw from u2
    draw_card(state, "u1", 0)
    
    assert len(p2.hand) == p2_initial_hand_size - 1
    
    # Ensure no pairs in p1's hand after drawing
    ranks = [card.rank for card in p1.hand]
    assert len(ranks) == len(set(ranks))
    
    # Turn should advance to u2
    assert state.turn_index == 1


def test_game_over():
    user_ids = ["u1", "u2"]
    state = start_game(user_ids, rng=random.Random(42))
    
    # Manually finish one player
    state.players[0].is_finished = True
    
    # Simulate a turn advancement check
    from app.games.papaz_kacti import _advance_turn_if_needed
    _advance_turn_if_needed(state)
    
    assert state.status == "finished"
    assert state.loser_user_id == "u2"

def test_start_game_3_players():
    user_ids = ["u1", "u2", "u3"]
    state = start_game(user_ids, rng=random.Random(42))
    assert state.status == "active"
    assert len(state.players) == 3
    # Initial dealing checks
    for player in state.players:
        ranks = [card.rank for card in player.hand]
        assert len(ranks) == len(set(ranks))

def test_start_game_4_players():
    user_ids = ["u1", "u2", "u3", "u4"]
    state = start_game(user_ids, rng=random.Random(42))
    assert state.status == "active"
    assert len(state.players) == 4
    for player in state.players:
        ranks = [card.rank for card in player.hand]
        assert len(ranks) == len(set(ranks))

def test_skip_finished_players():
    user_ids = ["u1", "u2", "u3"]
    state = start_game(user_ids, rng=random.Random(42))
    state.players[0].hand = []
    state.players[0].is_finished = True
    
    state.players[1].hand = [state.players[1].hand[0]]
    state.players[2].hand = [state.players[2].hand[0], state.players[2].hand[1]]
    
    # turn is 1 (u2)
    state.turn_index = 1
    # u2 draws from u3
    draw_card(state, "u2", 0)
    
    # turn advances to next active player. u1 is finished, so it should be u3
    assert state.turn_index == 2

def test_last_two_players_turn():
    user_ids = ["u1", "u2", "u3"]
    state = start_game(user_ids, rng=random.Random(42))
    state.players[0].is_finished = True
    state.turn_index = 1
    # U2 turn
    draw_card(state, "u2", 0)
    # advances to U3
    assert state.turn_index == 2
    # U3 turn
    draw_card(state, "u3", 0)
    # advances to U2
    assert state.turn_index == 1
