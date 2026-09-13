from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from roulette_lab.dashboard import (
    DashboardInputs,
    BankrollView,
    FairnessView,
    WheelView,
    build_bankroll_view,
    build_fairness_view,
    build_wheel_view,
    validate_dashboard_inputs,
)
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
