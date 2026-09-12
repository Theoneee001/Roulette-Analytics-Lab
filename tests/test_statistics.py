from collections import Counter

import numpy as np
import pytest
import scipy.stats

from roulette_lab.statistics import (
    FairnessResult,
    MaxCountResult,
    PosteriorEstimate,
    chi_square_fairness,
    dirichlet_posterior,
    max_count_test,
    monte_carlo_global_pvalue,
    split_spin_history,
)
from roulette_lab.wheels import WheelKind, make_fair_wheel


def test_chi_square_matches_scipy():
    counts = np.array([12] * 36 + [13])
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    result = chi_square_fairness(counts, wheel)
    expected = scipy.stats.chisquare(counts, np.full(37, counts.sum() / 37))

    assert isinstance(result, FairnessResult)
    assert result.statistic == pytest.approx(expected.statistic)
    assert result.p_value == pytest.approx(expected.pvalue)
    assert result.degrees_of_freedom == 36
    assert result.asymptotic_valid is True
    np.testing.assert_allclose(result.expected_counts, counts.sum() / 37)
    assert result.cramers_v == pytest.approx(
        np.sqrt(expected.statistic / (counts.sum() * 36))
    )


def test_small_expected_counts_require_monte_carlo():
    result = chi_square_fairness(
        np.bincount(np.arange(20) % 37, minlength=37),
        make_fair_wheel(WheelKind.EUROPEAN),
    )

    assert result.asymptotic_valid is False
    assert result.warning is not None
    assert "Monte Carlo" in result.warning


def test_monte_carlo_global_pvalue_uses_add_one_correction():
    counts = np.array([9] + [2] * 36)
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    simulations = 19

    observed = scipy.stats.chisquare(counts, np.full(37, counts.sum() / 37)).statistic
    expected_rng = np.random.default_rng(421)
    samples = expected_rng.multinomial(
        counts.sum(), np.full(37, 1 / 37), size=simulations
    )
    expected_statistics = ((samples - counts.sum() / 37) ** 2 / (counts.sum() / 37)).sum(
        axis=1
    )
    expected = (1 + np.count_nonzero(expected_statistics >= observed)) / (
        simulations + 1
    )

    actual = monte_carlo_global_pvalue(
        counts, wheel, simulations, np.random.default_rng(421)
    )

    assert actual == expected


def test_max_count_test_is_reproducible():
    counts = np.array([25] + [10] * 36)
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    first = max_count_test(counts, wheel, 4_000, np.random.default_rng(71))
    second = max_count_test(counts, wheel, 4_000, np.random.default_rng(71))

    assert isinstance(first, MaxCountResult)
    assert first == second
    assert first.familywise_p_value >= first.naive_p_value
    assert first.bonferroni_p_value >= first.naive_p_value


def test_max_count_test_uses_selected_maximum_and_binomial_references():
    counts = np.array([15] + [3] * 36)
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    result = max_count_test(counts, wheel, 31, np.random.default_rng(62))

    expected_naive = scipy.stats.binom.sf(14, counts.sum(), 1 / 37)
    assert result.observed_max == 15
    assert result.naive_p_value == pytest.approx(expected_naive)
    assert result.bonferroni_p_value == pytest.approx(min(1.0, 37 * expected_naive))
    assert 1 / 32 <= result.familywise_p_value <= 1


def test_dirichlet_posterior_uses_beta_marginals():
    counts = np.array([2, 0, 1])

    result = dirichlet_posterior(counts, prior_strength=1.0, level=0.90)

    total_concentration = counts.sum() + 3
    expected_lower, expected_upper = scipy.stats.beta.interval(
        0.90, counts[0] + 1, total_concentration - counts[0] - 1
    )
    assert isinstance(result, PosteriorEstimate)
    assert result.posterior_means == pytest.approx((3 / 6, 1 / 6, 2 / 6))
    assert result.lower_bounds[0] == pytest.approx(expected_lower)
    assert result.upper_bounds[0] == pytest.approx(expected_upper)
    assert result.prior_strength == 1.0
    assert result.level == 0.90


@pytest.mark.parametrize(
    "counts",
    [
        np.array([1] * 36),
        np.array([1.0] * 37),
        np.array([1] * 36 + [-1]),
        np.zeros(37, dtype=int),
        np.ones((37, 1), dtype=int),
    ],
)
def test_count_analyses_reject_invalid_count_vectors(counts):
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    with pytest.raises(ValueError):
        chi_square_fairness(counts, wheel)


@pytest.mark.parametrize(
    "counts",
    [
        np.array([1.0, 2.0]),
        np.array([1, -1]),
        np.zeros(2, dtype=int),
        np.ones((2, 1), dtype=int),
    ],
)
def test_dirichlet_posterior_rejects_invalid_count_vectors(counts):
    with pytest.raises(ValueError):
        dirichlet_posterior(counts, prior_strength=1.0, level=0.95)


@pytest.mark.parametrize("simulations", [0, -1, 2.5, True])
def test_simulation_tests_reject_non_positive_integer_simulation_counts(simulations):
    counts = np.ones(37, dtype=int)
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    rng = np.random.default_rng(9)

    with pytest.raises(ValueError):
        monte_carlo_global_pvalue(counts, wheel, simulations, rng)
    with pytest.raises(ValueError):
        max_count_test(counts, wheel, simulations, rng)


def test_simulation_tests_require_an_explicit_generator():
    counts = np.ones(37, dtype=int)
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    with pytest.raises(TypeError, match="Generator"):
        monte_carlo_global_pvalue(counts, wheel, 10, None)
    with pytest.raises(TypeError, match="Generator"):
        max_count_test(counts, wheel, 10, np.random.RandomState(2))


@pytest.mark.parametrize(
    ("prior_strength", "level"),
    [
        (0.0, 0.95),
        (-1.0, 0.95),
        (float("nan"), 0.95),
        (1.0, 0.0),
        (1.0, 1.0),
        (1.0, float("inf")),
    ],
)
def test_dirichlet_posterior_validates_prior_strength_and_credible_level(
    prior_strength, level
):
    with pytest.raises(ValueError):
        dirichlet_posterior(np.array([1, 2]), prior_strength, level)


def test_split_spin_history_is_disjoint_exhaustive_and_reproducible():
    spins = np.array(["0", "4", "4", "12", "7", "0", "31", "18", "4", "9"])

    estimation_a, validation_a = split_spin_history(
        spins, 0.3, np.random.default_rng(87)
    )
    estimation_b, validation_b = split_spin_history(
        spins, 0.3, np.random.default_rng(87)
    )

    np.testing.assert_array_equal(estimation_a, estimation_b)
    np.testing.assert_array_equal(validation_a, validation_b)
    assert len(validation_a) == 3
    assert Counter(estimation_a) + Counter(validation_a) == Counter(spins)
    assert len(estimation_a) + len(validation_a) == len(spins)


@pytest.mark.parametrize("fraction", [0.0, 1.0, -0.1, 1.1, float("nan")])
def test_split_spin_history_rejects_invalid_validation_fraction(fraction):
    with pytest.raises(ValueError):
        split_spin_history(np.array([1, 2, 3, 4]), fraction, np.random.default_rng(1))


def test_split_spin_history_requires_one_dimensional_nonempty_data_and_generator():
    with pytest.raises(ValueError):
        split_spin_history(np.array([]), 0.5, np.random.default_rng(1))
    with pytest.raises(ValueError):
        split_spin_history(np.array([[1, 2]]), 0.5, np.random.default_rng(1))
    with pytest.raises(TypeError, match="Generator"):
        split_spin_history(np.array([1, 2]), 0.5, None)
