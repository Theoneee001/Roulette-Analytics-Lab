from dataclasses import FrozenInstanceError, replace

import numpy as np
import pytest

from roulette_lab.bankroll import (
    BankrollConfig,
    BankrollSimulation,
    RiskSummary,
    StrategyKind,
    simulate_bankroll,
    summarize_bankroll,
)
from roulette_lab.bets import BetKind, SpecialRule, expected_net_return, house_edge, make_standard_bet
from roulette_lab.wheels import (
    WheelKind,
    make_biased_wheel,
    make_fair_wheel,
    wheel_with_single_pocket_probability,
)


def test_no_edge_kelly_places_no_bet():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), wheel)
    config = BankrollConfig(
        initial_bankroll=1_000,
        base_stake=10,
        spins=50,
        paths=20,
        strategy=StrategyKind.KELLY,
        estimated_win_probability=1 / 37,
    )

    result = simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(4))

    np.testing.assert_allclose(result.paths, 1_000)


def test_stop_loss_freezes_a_path_after_threshold():
    wheel = wheel_with_single_pocket_probability(
        make_fair_wheel(WheelKind.EUROPEAN), "17", 0.0
    )
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), wheel)
    config = BankrollConfig(
        initial_bankroll=100,
        base_stake=20,
        spins=20,
        paths=1,
        strategy=StrategyKind.FLAT,
        stop_loss=60,
    )

    result = simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(1))

    hit = np.flatnonzero(result.paths[0] <= 60)[0]
    assert np.unique(result.paths[0, hit:]).size == 1


def test_fixed_seed_reproduces_paths():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.RED, (), wheel)
    config = BankrollConfig(
        initial_bankroll=500,
        base_stake=5,
        spins=30,
        paths=10,
        strategy=StrategyKind.FLAT,
    )

    first = simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(19))
    second = simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(19))

    np.testing.assert_array_equal(first.paths, second.paths)


def test_custom_odds_are_explicit_and_change_only_simulated_payout():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), wheel)
    standard = BankrollConfig(
        initial_bankroll=500,
        base_stake=5,
        spins=1,
        paths=10_000,
        strategy=StrategyKind.FLAT,
    )
    custom = replace(standard, custom_net_odds=40)

    standard_result = simulate_bankroll(
        standard, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(12)
    )
    custom_result = simulate_bankroll(
        custom, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(12)
    )

    assert custom_result.payout_label == "Custom hypothetical odds: 40:1"
    assert standard_result.payout_label == "Casino standard odds: 35:1"
    assert standard_result.paths[:, -1].max() == 675
    assert custom_result.paths[:, -1].max() == 700
    assert bet.net_odds == 35
    assert house_edge(wheel, bet, SpecialRule.STANDARD) == pytest.approx(1 / 37)


def test_martingale_doubles_after_losses_and_reverse_martingale_after_wins():
    losing_wheel = wheel_with_single_pocket_probability(
        make_fair_wheel(WheelKind.EUROPEAN), "17", 0.0
    )
    winning_wheel = wheel_with_single_pocket_probability(
        make_fair_wheel(WheelKind.EUROPEAN), "17", 1.0
    )
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), losing_wheel)
    martingale = BankrollConfig(100, 5, 3, 1, StrategyKind.MARTINGALE)
    reverse = BankrollConfig(100, 5, 3, 1, StrategyKind.REVERSE_MARTINGALE)

    martingale_result = simulate_bankroll(
        martingale, losing_wheel, bet, SpecialRule.STANDARD, np.random.default_rng(3)
    )
    reverse_result = simulate_bankroll(
        reverse, winning_wheel, bet, SpecialRule.STANDARD, np.random.default_rng(3)
    )

    np.testing.assert_array_equal(martingale_result.paths[0], [100, 95, 85, 65])
    np.testing.assert_array_equal(reverse_result.paths[0], [100, 275, 625, 1325])


@pytest.mark.parametrize(
    ("strategy", "expected_terminal"),
    [
        (StrategyKind.FULL_KELLY, 345),
        (StrategyKind.HALF_KELLY, 205),
        (StrategyKind.QUARTER_KELLY, 135),
    ],
)
def test_fractional_kelly_uses_estimated_probability_and_rounds_down_to_chips(
    strategy, expected_terminal
):
    wheel = wheel_with_single_pocket_probability(
        make_fair_wheel(WheelKind.EUROPEAN), "17", 1.0
    )
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), wheel)
    config = BankrollConfig(
        initial_bankroll=100,
        base_stake=5,
        spins=1,
        paths=1,
        strategy=strategy,
        estimated_win_probability=0.1,
        min_chip=1,
    )

    result = simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(1))

    assert result.paths[0, -1] == expected_terminal


def test_chip_rounding_respects_available_bankroll_and_freezes_when_no_chip_is_affordable():
    wheel = wheel_with_single_pocket_probability(
        make_fair_wheel(WheelKind.EUROPEAN), "17", 0.0
    )
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), wheel)
    config = BankrollConfig(
        initial_bankroll=12,
        base_stake=7,
        spins=4,
        paths=1,
        strategy=StrategyKind.FLAT,
        min_chip=5,
        table_limit=10,
    )

    result = simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(7))

    np.testing.assert_array_equal(result.paths[0], [12, 7, 2, 2, 2])


def test_en_prison_keeps_the_full_stake_in_play_after_zero_including_repeated_zero():
    base = make_fair_wheel(WheelKind.EUROPEAN)
    probabilities = np.zeros(len(base.labels))
    probabilities[base.labels.index("0")] = 0.5
    probabilities[base.labels.index("1")] = 0.5
    zero_then_red = make_biased_wheel(WheelKind.EUROPEAN, probabilities)
    bet = make_standard_bet(BetKind.RED, (), zero_then_red)
    config = BankrollConfig(100, 10, 2, 20_000, StrategyKind.FLAT)

    prison = simulate_bankroll(
        config, zero_then_red, bet, SpecialRule.EN_PRISON, np.random.default_rng(22)
    )
    partage = simulate_bankroll(
        config, zero_then_red, bet, SpecialRule.LA_PARTAGE, np.random.default_rng(22)
    )
    zero_on_first_spin = prison.paths[:, 1] == 90

    assert zero_on_first_spin.any()
    deferred_settlements = prison.paths[zero_on_first_spin, 2]
    assert np.any(deferred_settlements == 90)
    assert np.any(deferred_settlements == 100)
    assert set(np.unique(deferred_settlements)) <= {90, 100}
    assert np.any(partage.paths[:, 1] == 95)


def test_en_prison_settlement_uses_the_imprisoned_stake_for_progression():
    wheel = _three_outcome_wheel()
    bet = make_standard_bet(BetKind.RED, (), wheel)
    martingale = BankrollConfig(100, 10, 3, 1, StrategyKind.MARTINGALE)
    reverse = BankrollConfig(100, 10, 3, 1, StrategyKind.REVERSE_MARTINGALE)

    zero_loss_loss = simulate_bankroll(
        martingale, wheel, bet, SpecialRule.EN_PRISON, np.random.default_rng(88)
    )
    zero_win_win = simulate_bankroll(
        reverse, wheel, bet, SpecialRule.EN_PRISON, np.random.default_rng(11)
    )

    np.testing.assert_array_equal(zero_loss_loss.paths[0], [100, 90, 90, 70])
    np.testing.assert_array_equal(zero_win_win.paths[0], [100, 90, 100, 120])


def test_repeated_en_prison_zero_preserves_the_original_stake_for_progression():
    wheel = _three_outcome_wheel()
    bet = make_standard_bet(BetKind.RED, (), wheel)
    martingale = BankrollConfig(100, 10, 4, 1, StrategyKind.MARTINGALE)
    reverse = BankrollConfig(100, 10, 4, 1, StrategyKind.REVERSE_MARTINGALE)

    zero_zero_loss_loss = simulate_bankroll(
        martingale, wheel, bet, SpecialRule.EN_PRISON, np.random.default_rng(168)
    )
    zero_zero_win_win = simulate_bankroll(
        reverse, wheel, bet, SpecialRule.EN_PRISON, np.random.default_rng(111)
    )

    np.testing.assert_array_equal(zero_zero_loss_loss.paths[0], [100, 90, 90, 90, 70])
    np.testing.assert_array_equal(zero_zero_win_win.paths[0], [100, 90, 90, 100, 120])


def test_en_prison_horizon_marks_a_recoverable_stake_to_conditional_equity():
    wheel = _three_outcome_wheel()
    bet = make_standard_bet(BetKind.RED, (), wheel)
    config = BankrollConfig(10, 10, 1, 1, StrategyKind.FLAT)

    simulation = simulate_bankroll(
        config, wheel, bet, SpecialRule.EN_PRISON, np.random.default_rng(2)
    )
    summary = summarize_bankroll(simulation)

    np.testing.assert_array_equal(simulation.paths[0], [10, 0])
    np.testing.assert_array_equal(simulation.equity_paths[0], [10, 5])
    np.testing.assert_array_equal(simulation.unresolved_stakes, [10])
    assert summary.terminal_mean == pytest.approx(5)
    assert summary.probability_of_loss == pytest.approx(1.0)
    assert summary.probability_of_ruin == pytest.approx(0.0)
    assert summary.expected_maximum_drawdown == pytest.approx(0.5)


def test_kelly_recalculates_from_liquid_cash_after_an_en_prison_loss():
    wheel = _three_outcome_wheel()
    bet = make_standard_bet(BetKind.RED, (), wheel)
    config = BankrollConfig(
        100,
        10,
        3,
        1,
        StrategyKind.KELLY,
        estimated_win_probability=0.75,
    )

    simulation = simulate_bankroll(
        config, wheel, bet, SpecialRule.EN_PRISON, np.random.default_rng(88)
    )

    np.testing.assert_array_equal(simulation.paths[0], [100, 50, 50, 25])


def test_non_en_prison_equity_paths_equal_liquid_cash_paths():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.RED, (), wheel)
    config = BankrollConfig(100, 5, 3, 4, StrategyKind.FLAT)

    simulation = simulate_bankroll(
        config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(8)
    )

    np.testing.assert_array_equal(simulation.equity_paths, simulation.paths)
    np.testing.assert_array_equal(simulation.unresolved_stakes, np.zeros(4))


def test_bankroll_simulation_equality_compares_numpy_values_safely():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.RED, (), wheel)
    config = BankrollConfig(100, 5, 10, 10, StrategyKind.FLAT)

    first = simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(71))
    same = simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(71))
    different = simulate_bankroll(
        config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(72)
    )

    assert first == same
    assert first != different
    assert first.__eq__(object()) is NotImplemented


def test_kelly_allows_an_unused_base_stake_above_table_limit_but_caps_the_bet():
    wheel = wheel_with_single_pocket_probability(
        make_fair_wheel(WheelKind.EUROPEAN), "17", 0.0
    )
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), wheel)

    with pytest.raises(ValueError, match="base_stake"):
        BankrollConfig(100, 20, 1, 1, StrategyKind.FLAT, table_limit=10)

    kelly = BankrollConfig(
        100,
        20,
        1,
        1,
        StrategyKind.KELLY,
        estimated_win_probability=1.0,
        table_limit=10,
    )
    simulation = simulate_bankroll(
        kelly, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(1)
    )

    np.testing.assert_array_equal(simulation.paths[0], [100, 90])


def test_special_rule_compatibility_is_validated_before_simulation():
    wheel = make_fair_wheel(WheelKind.AMERICAN)
    bet = make_standard_bet(BetKind.RED, (), wheel)
    config = BankrollConfig(100, 5, 1, 1, StrategyKind.FLAT)

    with pytest.raises(ValueError, match="European even-money"):
        simulate_bankroll(config, wheel, bet, SpecialRule.EN_PRISON, np.random.default_rng(1))


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"initial_bankroll": True}, "initial_bankroll"),
        ({"initial_bankroll": 0}, "initial_bankroll"),
        ({"base_stake": float("nan")}, "base_stake"),
        ({"spins": True}, "spins"),
        ({"paths": 2.5}, "paths"),
        ({"min_chip": float("inf")}, "min_chip"),
        ({"table_limit": 0.5, "min_chip": 1}, "table_limit"),
        ({"base_stake": 11, "table_limit": 10}, "base_stake"),
        ({"stop_loss": 100}, "stop_loss"),
        ({"take_profit": 100}, "take_profit"),
        ({"custom_net_odds": True}, "custom_net_odds"),
        ({"custom_net_odds": -1}, "custom_net_odds"),
    ],
)
def test_bankroll_config_rejects_invalid_values(kwargs, message):
    values = {
        "initial_bankroll": 100,
        "base_stake": 10,
        "spins": 2,
        "paths": 2,
        "strategy": StrategyKind.FLAT,
    }
    values.update(kwargs)

    with pytest.raises(ValueError, match=message):
        BankrollConfig(**values)


@pytest.mark.parametrize("strategy", list(StrategyKind))
def test_kelly_strategies_require_a_finite_probability_in_the_unit_interval(strategy):
    values = dict(initial_bankroll=100, base_stake=10, spins=2, paths=2, strategy=strategy)
    if strategy in {
        StrategyKind.FULL_KELLY,
        StrategyKind.HALF_KELLY,
        StrategyKind.QUARTER_KELLY,
    }:
        with pytest.raises(ValueError, match="estimated_win_probability"):
            BankrollConfig(**values)

        for probability in (True, float("nan"), float("inf"), -0.01, 1.01):
            with pytest.raises(ValueError, match="estimated_win_probability"):
                BankrollConfig(**(values | {"estimated_win_probability": probability}))
    else:
        assert BankrollConfig(**values).estimated_win_probability is None


def test_simulation_and_summary_are_immutable_and_path_dimensions_include_initial_capital():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.RED, (), wheel)
    config = BankrollConfig(100, 5, 3, 4, StrategyKind.FLAT)

    simulation = simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(8))
    summary = summarize_bankroll(simulation)

    assert isinstance(simulation, BankrollSimulation)
    assert isinstance(summary, RiskSummary)
    assert simulation.paths.shape == (4, 4)
    assert np.all(simulation.paths[:, 0] == 100)
    assert simulation.paths.flags.writeable is False
    assert simulation.equity_paths.flags.writeable is False
    assert simulation.unresolved_stakes.flags.writeable is False
    with pytest.raises(ValueError):
        simulation.paths[0, 0] = 0
    with pytest.raises(ValueError):
        simulation.equity_paths[0, 0] = 0
    with pytest.raises(ValueError):
        simulation.unresolved_stakes[0] = 0
    with pytest.raises(FrozenInstanceError):
        config.base_stake = 1
    assert summary.path_count == 4
    assert summary.spin_count == 3
    assert np.isfinite(summary.terminal_cvar_shortfall)
    assert summary.terminal_cvar_shortfall >= 0.0


def test_risk_summary_maximum_drawdown_uses_running_path_peaks():
    config = BankrollConfig(100, 10, 3, 2, StrategyKind.FLAT)
    paths = np.array([[100.0, 150.0, 120.0, 135.0], [100.0, 80.0, 60.0, 90.0]])
    simulation = BankrollSimulation(config=config, paths=paths, payout_label="Casino standard odds: 1:1")

    summary = summarize_bankroll(simulation)

    assert summary.expected_maximum_drawdown == pytest.approx((0.2 + 0.4) / 2)
    assert summary.median_maximum_drawdown == pytest.approx(0.3)
    assert summary.probability_of_loss == pytest.approx(0.5)
    assert summary.probability_of_ruin == pytest.approx(0.0)
    assert summary.terminal_cvar_shortfall == pytest.approx(10.0)


def test_risk_summary_prior_positional_constructor_defaults_terminal_cvar():
    summary = RiskSummary(
        100.0,
        99.0,
        5.0,
        90.0,
        110.0,
        0.25,
        0.01,
        0.30,
        0.20,
        50,
        100,
    )

    assert summary.probability_of_loss == pytest.approx(0.25)
    assert summary.path_count == 50
    assert summary.spin_count == 100
    assert summary.terminal_cvar_shortfall == 0.0


def test_risk_summary_prior_keyword_constructor_defaults_terminal_cvar():
    summary = RiskSummary(
        terminal_mean=100.0,
        terminal_median=99.0,
        terminal_standard_deviation=5.0,
        terminal_percentile_5=90.0,
        terminal_percentile_95=110.0,
        probability_of_loss=0.25,
        probability_of_ruin=0.01,
        expected_maximum_drawdown=0.30,
        median_maximum_drawdown=0.20,
        path_count=50,
        spin_count=100,
    )

    assert summary.terminal_cvar_shortfall == 0.0


def test_one_spin_mean_agrees_with_analytical_expectation_within_five_mc_standard_errors():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), wheel)
    initial = 100
    stake = 5
    paths = 100_000
    config = BankrollConfig(initial, stake, 1, paths, StrategyKind.FLAT)

    simulation = simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(901))
    expected_terminal = initial + stake * expected_net_return(wheel, bet, SpecialRule.STANDARD)
    win_probability = 1 / 37
    expected_profit = expected_terminal - initial
    payout = bet.net_odds * stake
    variance = (
        win_probability * (payout - expected_profit) ** 2
        + (1 - win_probability) * (-stake - expected_profit) ** 2
    )
    standard_error = np.sqrt(variance / paths)

    assert abs(simulation.paths[:, -1].mean() - expected_terminal) <= 5 * standard_error


def test_simulation_requires_an_explicit_numpy_generator():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.RED, (), wheel)
    config = BankrollConfig(100, 5, 1, 1, StrategyKind.FLAT)

    with pytest.raises(TypeError, match="Generator"):
        simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, None)


def test_bankroll_interfaces_are_exported_from_the_package():
    from roulette_lab import (  # noqa: PLC0415
        BankrollConfig as ExportedBankrollConfig,
        BankrollSimulation as ExportedBankrollSimulation,
        RiskSummary as ExportedRiskSummary,
        StrategyKind as ExportedStrategyKind,
        simulate_bankroll as exported_simulate_bankroll,
        summarize_bankroll as exported_summarize_bankroll,
    )

    assert ExportedBankrollConfig is BankrollConfig
    assert ExportedBankrollSimulation is BankrollSimulation
    assert ExportedRiskSummary is RiskSummary
    assert ExportedStrategyKind is StrategyKind
    assert exported_simulate_bankroll is simulate_bankroll
    assert exported_summarize_bankroll is summarize_bankroll


def _three_outcome_wheel():
    base = make_fair_wheel(WheelKind.EUROPEAN)
    probabilities = np.zeros(len(base.labels))
    probabilities[base.labels.index("0")] = 1 / 3
    probabilities[base.labels.index("1")] = 1 / 3
    probabilities[base.labels.index("2")] = 1 / 3
    return make_biased_wheel(WheelKind.EUROPEAN, probabilities)
