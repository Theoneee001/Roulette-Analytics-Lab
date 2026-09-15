from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from roulette_lab.bets import BetKind, SpecialRule, make_standard_bet
from roulette_lab.experiment import (
    ExperimentState,
    advance_experiment,
    new_experiment,
    reset_experiment,
)
from roulette_lab.wheels import WheelKind, make_biased_wheel, make_fair_wheel


@pytest.fixture
def fair_wheel():
    return make_fair_wheel(WheelKind.EUROPEAN)


@pytest.fixture
def straight_17(fair_wheel):
    return make_standard_bet(BetKind.STRAIGHT, ("17",), fair_wheel)


def test_single_spins_equal_one_batch_for_the_same_seed(fair_wheel, straight_17):
    state = new_experiment(seed=42, initial_bankroll=1_000.0)
    singles = state

    for _ in range(10):
        singles = advance_experiment(
            singles, fair_wheel, straight_17, SpecialRule.STANDARD, 10.0, 1
        )
    batch = advance_experiment(
        state, fair_wheel, straight_17, SpecialRule.STANDARD, 10.0, 10
    )

    assert singles.history == batch.history
    assert singles.bankroll == batch.bankroll


def test_reset_restores_seed_and_empty_history(fair_wheel, straight_17):
    advanced = advance_experiment(
        new_experiment(7, 500.0),
        fair_wheel,
        straight_17,
        SpecialRule.STANDARD,
        5.0,
        4,
    )

    assert reset_experiment(advanced) == new_experiment(7, 500.0)


def test_state_is_frozen_and_validates_history_shape():
    state = new_experiment(3, 50.0)

    with pytest.raises(FrozenInstanceError):
        state.bankroll = 0.0
    with pytest.raises(ValueError, match="history"):
        ExperimentState(3, 50.0, history=("17", ""), bankroll=50.0)
    with pytest.raises(ValueError, match="history"):
        ExperimentState(3, 50.0, history=("17", 18), bankroll=50.0)


def test_counts_follow_wheel_label_order_and_indicators_mark_hits(fair_wheel):
    state = ExperimentState(3, 50.0, history=("17", "0", "17"), bankroll=50.0)

    counts = state.counts(fair_wheel)

    assert counts.dtype == np.int64
    assert counts.shape == (len(fair_wheel.labels),)
    assert counts[0] == 1
    assert counts[fair_wheel.labels.index("17")] == 2
    np.testing.assert_array_equal(state.indicators("17"), np.array([1, 0, 1]))


def test_advance_rejects_history_labels_not_present_on_wheel(fair_wheel, straight_17):
    state = ExperimentState(3, 50.0, history=("37",), bankroll=50.0)

    with pytest.raises(ValueError, match="history"):
        advance_experiment(
            state, fair_wheel, straight_17, SpecialRule.STANDARD, 5.0, 1
        )


def test_experiment_continues_recording_spins_after_bankroll_reaches_zero(straight_17):
    wheel = _single_outcome_wheel("0")
    state = advance_experiment(
        new_experiment(2, 5.0), wheel, straight_17, SpecialRule.STANDARD, 5.0, 3
    )

    assert state.bankroll == 0.0
    assert state.history == ("0", "0", "0")


def test_la_partage_zero_settles_as_half_loss():
    wheel = _single_outcome_wheel("0")
    bet = make_standard_bet(BetKind.RED, (), wheel)

    state = advance_experiment(
        new_experiment(5, 100.0), wheel, bet, SpecialRule.LA_PARTAGE, 10.0, 1
    )

    assert state.history == ("0",)
    assert state.bankroll == 95.0


def test_en_prison_defers_zero_stake_until_a_later_nonzero_outcome():
    wheel = _zero_or_red_wheel()
    bet = make_standard_bet(BetKind.RED, (), wheel)

    state = advance_experiment(
        new_experiment(8, 100.0), wheel, bet, SpecialRule.EN_PRISON, 10.0, 2
    )

    assert state.history == ("0", "1")
    assert state.bankroll == 100.0


@pytest.mark.parametrize(
    "seed,initial_bankroll",
    [
        (True, 10.0),
        (-1, 10.0),
        (1, 0.0),
        (1, float("inf")),
    ],
)
def test_new_experiment_rejects_invalid_seed_and_bankroll(seed, initial_bankroll):
    with pytest.raises(ValueError):
        new_experiment(seed, initial_bankroll)


@pytest.mark.parametrize("stake,count", [(0.0, 1), (5.0, 0), (True, 1), (5.0, True)])
def test_advance_rejects_invalid_stake_and_count(fair_wheel, straight_17, stake, count):
    with pytest.raises(ValueError):
        advance_experiment(
            new_experiment(1, 10.0),
            fair_wheel,
            straight_17,
            SpecialRule.STANDARD,
            stake,
            count,
        )


def _single_outcome_wheel(label):
    base = make_fair_wheel(WheelKind.EUROPEAN)
    probabilities = np.zeros(len(base.labels))
    probabilities[base.labels.index(label)] = 1.0
    return make_biased_wheel(WheelKind.EUROPEAN, probabilities)


def _zero_or_red_wheel():
    base = make_fair_wheel(WheelKind.EUROPEAN)
    probabilities = np.zeros(len(base.labels))
    probabilities[base.labels.index("0")] = 0.5
    probabilities[base.labels.index("1")] = 0.5
    return make_biased_wheel(WheelKind.EUROPEAN, probabilities)
