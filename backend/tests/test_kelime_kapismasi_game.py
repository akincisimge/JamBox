from datetime import UTC, datetime, timedelta

import pytest

from app.games.kelime_kapismasi import (
    COUNTDOWN_SECONDS,
    RESULT_SECONDS,
    STAGE_PLAN,
    make_round,
    remaining_seconds,
    start_game,
    submit_word,
    sync_state,
)

BASE_TIME = datetime(2026, 8, 4, 10, 0, tzinfo=UTC)


def rounds():
    values = []
    for index in range(6):
        min_length = STAGE_PLAN[index][2]
        word = "a" * min_length
        values.append(
            make_round(
                index,
                round_id=f"round-{index + 1}",
                letters="a" * (min_length + 2),
                valid_words={word},
            )
        )
    return values


def test_start_game_requires_exactly_two_unique_players():
    with pytest.raises(ValueError, match="tam olarak 2"):
        start_game(["a"], rounds(), now=BASE_TIME)
    with pytest.raises(ValueError, match="benzersiz"):
        start_game(["a", "a"], rounds(), now=BASE_TIME)


def test_stage_plan_is_two_easy_two_medium_two_hard():
    assert [item[0] for item in STAGE_PLAN] == [
        "easy",
        "easy",
        "medium",
        "medium",
        "hard",
        "hard",
    ]


def test_countdown_moves_to_playing_at_same_server_time():
    state = start_game(["a", "b"], rounds(), now=BASE_TIME)

    assert state.status == "countdown"
    assert remaining_seconds(state, now=BASE_TIME) == COUNTDOWN_SECONDS

    changed = sync_state(
        state,
        now=BASE_TIME + timedelta(seconds=COUNTDOWN_SECONDS),
    )

    assert changed is True
    assert state.status == "playing"
    assert remaining_seconds(state, now=BASE_TIME + timedelta(seconds=3)) == 45


def test_submit_word_validates_dictionary_letters_and_duplicates():
    state = start_game(["a", "b"], rounds(), now=BASE_TIME)
    play_time = BASE_TIME + timedelta(seconds=3)

    assert submit_word(state, "a", "AAA", now=play_time) == "aaa"

    with pytest.raises(ValueError, match="daha önce"):
        submit_word(state, "a", "aaa", now=play_time)
    with pytest.raises(ValueError, match="en az"):
        submit_word(state, "b", "aa", now=play_time)
    with pytest.raises(ValueError, match="verilen harflerle"):
        submit_word(state, "b", "aab", now=play_time)
    with pytest.raises(ValueError, match="sözlükte"):
        submit_word(state, "b", "aaaa", now=play_time)


def test_round_winner_gets_difficulty_points():
    state = start_game(["a", "b"], rounds(), now=BASE_TIME)
    play_time = BASE_TIME + timedelta(seconds=3)
    submit_word(state, "a", "aaa", now=play_time)

    round_end = play_time + timedelta(seconds=45)
    sync_state(state, now=round_end)

    assert state.status == "round_result"
    assert state.results[0].winner_user_id == "a"
    assert state.players[0].stage_points == 1
    assert state.results[0].players[0].words == ["aaa"]
    assert remaining_seconds(state, now=round_end) == RESULT_SECONDS


def test_draw_splits_stage_points():
    state = start_game(["a", "b"], rounds(), now=BASE_TIME)
    play_time = BASE_TIME + timedelta(seconds=3)
    submit_word(state, "a", "aaa", now=play_time)
    submit_word(state, "b", "aaa", now=play_time)

    sync_state(state, now=play_time + timedelta(seconds=45))

    assert state.results[0].winner_user_id is None
    assert state.players[0].stage_points == 0.5
    assert state.players[1].stage_points == 0.5


def test_result_phase_automatically_starts_next_stage():
    state = start_game(["a", "b"], rounds(), now=BASE_TIME)
    play_time = BASE_TIME + timedelta(seconds=3)
    submit_word(state, "a", "aaa", now=play_time)
    next_countdown = play_time + timedelta(seconds=45 + RESULT_SECONDS)

    sync_state(state, now=next_countdown)

    assert state.stage_index == 1
    assert state.status == "countdown"
    assert state.players[0].submissions == []


def test_sync_can_catch_up_multiple_expired_phases():
    state = start_game(["a", "b"], rounds(), now=BASE_TIME)

    sync_state(
        state,
        now=BASE_TIME
        + timedelta(
            seconds=(
                COUNTDOWN_SECONDS
                + 45
                + RESULT_SECONDS
                + COUNTDOWN_SECONDS
            )
        ),
    )

    assert state.stage_index == 1
    assert state.status == "playing"


def test_game_finishes_after_six_stages_and_uses_total_score():
    state = start_game(["a", "b"], rounds(), now=BASE_TIME)
    cursor = BASE_TIME

    for _, duration, min_length, _ in STAGE_PLAN:
        cursor += timedelta(seconds=COUNTDOWN_SECONDS)
        submit_word(state, "a", "a" * min_length, now=cursor)
        cursor += timedelta(seconds=duration)
        sync_state(state, now=cursor)
        cursor += timedelta(seconds=RESULT_SECONDS)
        sync_state(state, now=cursor)

    assert state.status == "finished"
    assert state.winner_user_id == "a"
    assert state.players[0].stage_points == 12
    assert state.players[0].total_words == 6


def test_turkish_uppercase_i_normalization():
    round_spec = make_round(
        0,
        round_id="turkish-i",
        letters="İ L K",
        valid_words={"ilk"},
    )
    custom_rounds = [round_spec, *rounds()[1:]]
    state = start_game(["a", "b"], custom_rounds, now=BASE_TIME)

    assert (
        submit_word(
            state,
            "a",
            "İLK",
            now=BASE_TIME + timedelta(seconds=COUNTDOWN_SECONDS),
        )
        == "ilk"
    )
