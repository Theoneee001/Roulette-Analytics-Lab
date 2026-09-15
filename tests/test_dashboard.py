from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from roulette_lab.dashboard import (
    DashboardInputs,
    BankrollView,
    LiveExperimentView,
    FairnessView,
    WheelView,
    build_bankroll_view,
    build_decision_risk_view,
    build_fairness_view,
    build_live_experiment_view,
    build_wheel_view,
    validate_dashboard_inputs,
)
from roulette_lab.bets import BetKind, SpecialRule, make_standard_bet
from roulette_lab.experiment import ExperimentState, advance_experiment, new_experiment
from roulette_lab.io import SpinDataset
from roulette_lab.wheels import WheelKind, make_fair_wheel


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_rejects_stop_loss_above_initial_bankroll():
    with pytest.raises(ValueError, match="below the initial bankroll"):
        validate_dashboard_inputs({"initial_bankroll": 500, "stop_loss": 600})


def test_dashboard_validation_preserves_zero_stop_loss_and_custom_odds_label():
    inputs = validate_dashboard_inputs(
        {
            "initial_bankroll": 500,
            "stop_loss": 0,
            "take_profit": 900,
            "odds_mode": "Custom hypothetical",
            "custom_net_odds": 40,
        }
    )

    assert inputs.stop_loss == 0
    assert inputs.custom_net_odds == 40


def test_wheel_view_uses_exact_standard_economics_even_with_custom_scenario_odds():
    inputs = replace(
        DashboardInputs.fast_test(),
        odds_mode="Custom hypothetical",
        custom_net_odds=40,
    )

    view = build_wheel_view(inputs)

    assert isinstance(view, WheelView)
    assert view.standard_house_edge == pytest.approx(1 / 37)
    assert view.simulation_payout_label == "Custom hypothetical odds: 40:1"
    assert "hypothetical" in view.scenario_notice.lower()


def test_wheel_view_exposes_canonical_table_geometry():
    european = build_wheel_view(DashboardInputs.fast_test())
    american = build_wheel_view(
        replace(DashboardInputs.fast_test(), wheel_kind="american", bias_probability=1 / 38)
    )

    assert european.zero_pockets == ("0",)
    assert american.zero_pockets == ("0", "00")
    assert list(european.table_geometry.columns) == ["low", "middle", "high"]
    assert european.table_geometry.iloc[0].tolist() == ["1", "2", "3"]
    assert european.table_geometry.iloc[-1].tolist() == ["34", "35", "36"]


def test_fairness_view_exposes_selection_warning():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    spins = ("17",) * 50 + tuple(label for label in wheel.labels for _ in range(2))
    dataset = SpinDataset(
        spin_indices=tuple(range(1, len(spins) + 1)),
        spins=spins,
        wheel_kind=wheel.kind,
        wheel_labels=wheel.labels,
        wheel_probabilities=tuple(wheel.probabilities),
    )

    view = build_fairness_view(dataset, DashboardInputs.fast_test())

    assert isinstance(view, FairnessView)
    assert "selected after observing" in view.selection_warning.lower()
    assert view.familywise_p_value >= view.naive_p_value
    assert set(view.counts.columns) == {"label", "observed", "expected", "residual"}


def test_fairness_view_warns_when_expected_counts_are_too_small():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    spins = tuple(wheel.labels[:20])
    dataset = SpinDataset(
        spin_indices=tuple(range(1, 21)),
        spins=spins,
        wheel_kind=wheel.kind,
        wheel_labels=wheel.labels,
        wheel_probabilities=tuple(wheel.probabilities),
    )

    view = build_fairness_view(dataset, DashboardInputs.fast_test())

    assert view.sample_warning is not None
    assert "Monte Carlo" in view.sample_warning


def test_bankroll_view_is_seeded_and_exposes_no_edge_kelly_state():
    inputs = replace(
        DashboardInputs.fast_test(),
        strategy="full_kelly",
        estimated_win_probability=1 / 37,
    )

    first = build_bankroll_view(inputs)
    second = build_bankroll_view(inputs)

    assert isinstance(first, BankrollView)
    np.testing.assert_array_equal(first.path_data, second.path_data)
    assert first.no_edge_message is not None
    assert np.all(first.path_data == inputs.initial_bankroll)


def test_dashboard_rejects_incompatible_special_rule_and_wheel():
    inputs = replace(
        DashboardInputs.fast_test(), wheel_kind="american", rule="la_partage"
    )

    with pytest.raises(ValueError, match="European even-money"):
        build_wheel_view(inputs)


def test_mobile_css_allows_titles_and_notices_to_wrap():
    source = (ROOT / "app.py").read_text(encoding="utf-8")

    assert "white-space: normal !important" in source
    assert "overflow-wrap: anywhere" in source
    assert "[data-baseweb=\"tab-list\"] { overflow-x: auto" in source


def test_live_view_updates_all_evidence_from_history():
    inputs = DashboardInputs.fast_test()
    wheel = make_fair_wheel(WheelKind(inputs.wheel_kind))
    bet = make_standard_bet(BetKind(inputs.bet_kind), inputs.selection, wheel)
    state = advance_experiment(
        new_experiment(inputs.seed, inputs.initial_bankroll),
        wheel,
        bet,
        SpecialRule(inputs.rule),
        10.0,
        50,
    )

    view = build_live_experiment_view(state, inputs)

    assert isinstance(view, LiveExperimentView)
    assert view.sample_size == 50
    assert len(view.running_frequency) == 50
    assert len(view.e_values) == 50
    assert 0 <= view.posterior.probability_positive_edge <= 1


def test_live_view_exposes_explicit_empty_history_state():
    inputs = DashboardInputs.fast_test()
    view = build_live_experiment_view(new_experiment(inputs.seed, inputs.initial_bankroll), inputs)

    assert view.sample_size == 0
    assert view.empty_message is not None


def test_decision_risk_uses_live_posterior_mean_for_frontier_and_fan():
    inputs = replace(DashboardInputs.fast_test(), paths=80, spins=40)
    losing = ExperimentState(
        inputs.seed,
        inputs.initial_bankroll,
        history=("0",) * 20,
        bankroll=inputs.initial_bankroll,
    )
    winning = ExperimentState(
        inputs.seed,
        inputs.initial_bankroll,
        history=("17",) * 20,
        bankroll=inputs.initial_bankroll,
    )

    losing_view = build_decision_risk_view(losing, inputs)
    winning_view = build_decision_risk_view(winning, inputs)

    assert losing_view.decision_probability == losing_view.posterior.posterior_mean
    assert winning_view.decision_probability == winning_view.posterior.posterior_mean
    assert losing_view.decision_probability != winning_view.decision_probability
    assert not np.array_equal(losing_view.bankroll.equity_data, winning_view.bankroll.equity_data)
    assert not losing_view.frontier.equals(winning_view.frontier)


def test_long_miss_history_retains_finite_log10_evidence_path():
    inputs = DashboardInputs.fast_test()
    state = ExperimentState(
        inputs.seed,
        inputs.initial_bankroll,
        history=("0",) * 1_000,
        bankroll=inputs.initial_bankroll,
    )

    view = build_live_experiment_view(state, inputs)

    expected_last = 1_000 * np.log((1 - inputs.target_probability) / (1 - 1 / 37)) / np.log(10)
    assert len(view.log10_evidence) == 1_000
    assert np.all(np.isfinite(view.log10_evidence))
    assert view.log10_evidence[-1] == pytest.approx(expected_last)
    assert view.log10_threshold == pytest.approx(np.log10(1 / inputs.alpha))


def test_live_evidence_includes_global_and_selection_aware_fairness():
    inputs = DashboardInputs.fast_test()
    state = ExperimentState(
        inputs.seed,
        inputs.initial_bankroll,
        history=("17",) * 12 + ("0",) * 8,
        bankroll=inputs.initial_bankroll,
    )

    view = build_live_experiment_view(state, inputs)

    assert isinstance(view.fairness, FairnessView)
    assert np.isfinite(view.fairness.chi_square_statistic)
    assert view.fairness.familywise_p_value >= view.fairness.naive_p_value
