import numpy as np
import pytest
import scipy.stats

from roulette_lab.decision import posterior_edge_summary


def test_posterior_edge_summary_matches_beta_distribution():
    result = posterior_edge_summary(
        hits=6,
        trials=100,
        prior_alpha=1.0,
        prior_beta=36.0,
        net_odds=35.0,
        level=0.95,
        lower_quantile=0.10,
        future_trials=100,
    )

    assert result.posterior_alpha == pytest.approx(7.0)
    assert result.posterior_beta == pytest.approx(130.0)
    assert result.break_even_probability == pytest.approx(1 / 36)
    assert result.posterior_mean == pytest.approx(7 / 137)
    assert result.probability_positive_edge == pytest.approx(
        scipy.stats.beta.sf(1 / 36, 7, 130)
    )
    assert result.plugin_kelly > 0
    assert 0 <= result.quantile_kelly <= result.plugin_kelly
    assert result.predictive_interval == tuple(
        int(value)
        for value in scipy.stats.betabinom.interval(0.95, 100, 7, 130)
    )


def test_fair_prior_with_no_data_allocates_no_robust_stake():
    result = posterior_edge_summary(0, 0, 1.0, 36.0, 35.0, 0.95, 0.10, 100)

    assert result.quantile_kelly == 0.0


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ((-1, 1, 1.0, 1.0, 1.0, 0.95, 0.1, 1), "hits"),
        ((2, 1, 1.0, 1.0, 1.0, 0.95, 0.1, 1), "hits"),
        ((0, 1.5, 1.0, 1.0, 1.0, 0.95, 0.1, 1), "trials"),
        ((0, 1, 0.0, 1.0, 1.0, 0.95, 0.1, 1), "prior_alpha"),
        ((0, 1, 1.0, np.inf, 1.0, 0.95, 0.1, 1), "prior_beta"),
        ((0, 1, 1.0, 1.0, 0.0, 0.95, 0.1, 1), "net_odds"),
        ((0, 1, 1.0, 1.0, 1.0, 1.0, 0.1, 1), "level"),
        ((0, 1, 1.0, 1.0, 1.0, 0.95, 0.0, 1), "lower_quantile"),
        ((0, 1, 1.0, 1.0, 1.0, 0.95, 0.1, True), "future_trials"),
    ],
)
def test_posterior_edge_summary_rejects_invalid_inputs(arguments, message):
    with pytest.raises(ValueError, match=message):
        posterior_edge_summary(*arguments)


def test_posterior_edge_summary_rejects_nonfinite_beta_shape_sum():
    largest_float = np.finfo(float).max

    with pytest.raises(ValueError, match="shape sums must be finite"):
        posterior_edge_summary(
            0, 0, largest_float, largest_float, 35.0, 0.95, 0.10, 1
        )


def test_posterior_edge_summary_accepts_practical_future_trials_maximum():
    result = posterior_edge_summary(
        6, 100, 1.0, 36.0, 35.0, 0.95, 0.10, 1_000_000
    )

    assert result.predictive_interval == (20_939, 93_554)


def test_posterior_edge_summary_rejects_future_trials_above_practical_maximum():
    with pytest.raises(ValueError, match=r"^future_trials must be at most 1000000\.$"):
        posterior_edge_summary(
            0, 0, 1.0, 36.0, 35.0, 0.95, 0.10, 1_000_001
        )


def test_decision_interface_is_exported_from_package():
    from roulette_lab import (  # noqa: PLC0415
        PosteriorEdgeSummary,
        posterior_edge_summary as exported_posterior_edge_summary,
    )
    from roulette_lab.decision import PosteriorEdgeSummary as DirectSummary

    assert PosteriorEdgeSummary is DirectSummary
    assert exported_posterior_edge_summary is posterior_edge_summary
