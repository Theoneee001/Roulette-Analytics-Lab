from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from roulette_lab.bankroll import BankrollConfig, StrategyKind, simulate_bankroll
from roulette_lab.bets import BetKind, SpecialRule, make_standard_bet
from roulette_lab.risk import build_risk_frontier, conditional_value_at_risk
from roulette_lab.wheels import WheelKind, make_fair_wheel


def test_cvar_is_mean_of_worst_terminal_losses():
    losses = np.array([-20.0, 0.0, 10.0, 30.0, 50.0])

    assert conditional_value_at_risk(losses, tail_probability=0.40) == pytest.approx(40.0)


@pytest.mark.parametrize(
    ("losses", "tail_probability", "message"),
    [
        ([], 0.05, "losses"),
        ([1.0, np.nan], 0.05, "losses"),
        ([1.0], 0.0, "tail_probability"),
        ([1.0], True, "tail_probability"),
    ],
)
def test_cvar_rejects_invalid_inputs(losses, tail_probability, message):
    with pytest.raises(ValueError, match=message):
        conditional_value_at_risk(losses, tail_probability)


def test_risk_frontier_has_one_sorted_point_per_fraction():
    base_config, wheel, bet, rule = _frontier_inputs()

    table = build_risk_frontier(
        base_config,
        wheel,
        bet,
        rule,
        fractions=[1.0, 0.25, 0.5],
        seed=7,
    )

    assert isinstance(table, pd.DataFrame)
    assert list(table["kelly_fraction_multiplier"]) == [0.25, 0.5, 1.0]
    assert {
        "terminal_mean",
        "terminal_median",
        "probability_of_loss",
        "expected_maximum_drawdown",
        "expected_log_growth",
        "terminal_cvar_shortfall",
    } <= set(table)
    assert np.all(table["terminal_cvar_shortfall"] >= 0.0)


def test_risk_frontier_resets_the_identical_seed_for_each_fraction():
    base_config, wheel, bet, rule = _frontier_inputs()

    table = build_risk_frontier(base_config, wheel, bet, rule, [0.25], seed=19)
    direct_config = replace(base_config, strategy=StrategyKind.QUARTER_KELLY)
    direct_simulation = simulate_bankroll(
        direct_config, wheel, bet, rule, np.random.default_rng(19)
    )

    assert table.loc[0, "terminal_mean"] == pytest.approx(
        direct_simulation.equity_paths[:, -1].mean()
    )


@pytest.mark.parametrize("fractions", [[], [0.75], [0.25, 0.25]])
def test_risk_frontier_rejects_unsupported_or_ambiguous_multipliers(fractions):
    base_config, wheel, bet, rule = _frontier_inputs()

    with pytest.raises(ValueError, match="fractions"):
        build_risk_frontier(base_config, wheel, bet, rule, fractions, seed=7)


def test_risk_interface_is_exported_from_package():
    from roulette_lab import (  # noqa: PLC0415
        build_risk_frontier as exported_build_risk_frontier,
        conditional_value_at_risk as exported_conditional_value_at_risk,
    )

    assert exported_build_risk_frontier is build_risk_frontier
    assert exported_conditional_value_at_risk is conditional_value_at_risk


def _frontier_inputs():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.RED, (), wheel)
    base_config = BankrollConfig(
        initial_bankroll=100.0,
        base_stake=5.0,
        spins=10,
        paths=100,
        strategy=StrategyKind.FLAT,
        estimated_win_probability=0.60,
    )
    return base_config, wheel, bet, SpecialRule.STANDARD
