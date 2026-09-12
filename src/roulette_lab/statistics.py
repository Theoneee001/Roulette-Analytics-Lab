"""Fairness and selection-aware bias analyses for roulette spin counts."""

from dataclasses import dataclass
from numbers import Integral, Real

import numpy as np
import scipy.stats
from numpy.typing import ArrayLike, NDArray

from .wheels import WheelSpec


@dataclass(frozen=True, slots=True)
class FairnessResult:
    """A Pearson chi-square goodness-of-fit result under a uniform wheel null."""

    statistic: float
    p_value: float
    degrees_of_freedom: int
    expected_counts: tuple[float, ...]
    pearson_residuals: tuple[float, ...]
    cramers_v: float
    asymptotic_valid: bool
    warning: str | None


@dataclass(frozen=True, slots=True)
class MaxCountResult:
    """A post-selection-aware test of the largest observed pocket count."""

    observed_max: int
    naive_p_value: float
    bonferroni_p_value: float
    familywise_p_value: float
    simulations: int


@dataclass(frozen=True, slots=True)
class PosteriorEstimate:
    """Marginal summaries from a symmetric Dirichlet posterior."""

    posterior_means: tuple[float, ...]
    lower_bounds: tuple[float, ...]
    upper_bounds: tuple[float, ...]
    prior_strength: float
    level: float


def _validated_wheel(wheel: WheelSpec) -> WheelSpec:
    if not isinstance(wheel, WheelSpec):
        raise TypeError("wheel must be a WheelSpec.")
    return wheel


def _validated_counts(
    counts: ArrayLike, pocket_count: int | None = None
) -> NDArray[np.int64]:
    values = np.asarray(counts)
    if values.ndim != 1:
        raise ValueError("Counts must be a one-dimensional integer array.")
    if pocket_count is not None and values.shape != (pocket_count,):
        raise ValueError(f"Expected counts for exactly {pocket_count} pockets.")
    if values.size == 0:
        raise ValueError("Counts must contain at least one pocket.")
    if not np.issubdtype(values.dtype, np.integer):
        raise ValueError("Counts must be integers.")
    if np.any(values < 0):
        raise ValueError("Counts must be non-negative.")

    total = values.sum(dtype=np.int64)
    if total <= 0:
        raise ValueError("Counts must have a positive total.")
    return values.astype(np.int64, copy=False)


def _validated_simulations(simulations: int) -> int:
    if isinstance(simulations, bool) or not isinstance(simulations, Integral):
        raise ValueError("simulations must be a positive integer.")
    if simulations <= 0:
        raise ValueError("simulations must be a positive integer.")
    return int(simulations)


def _validated_rng(rng: np.random.Generator) -> np.random.Generator:
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator.")
    return rng


def _validated_probability_input(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number strictly between zero and one.")
    value = float(value)
    if not np.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError(f"{name} must be a finite number strictly between zero and one.")
    return value


def _uniform_expected_counts(total: int, pocket_count: int) -> NDArray[np.float64]:
    return np.full(pocket_count, total / pocket_count, dtype=float)


def _pearson_statistic(
    counts: NDArray[np.int64], expected_counts: NDArray[np.float64]
) -> float:
    return float(np.sum((counts - expected_counts) ** 2 / expected_counts))


def chi_square_fairness(counts: ArrayLike, wheel: WheelSpec) -> FairnessResult:
    """Test whether pocket counts fit the uniform fair-wheel null hypothesis."""

    wheel = _validated_wheel(wheel)
    values = _validated_counts(counts, len(wheel.labels))
    total = int(values.sum())
    expected = _uniform_expected_counts(total, len(wheel.labels))
    chi_square = scipy.stats.chisquare(values, expected)
    residuals = (values - expected) / np.sqrt(expected)
    asymptotic_valid = bool(np.all(expected >= 5.0))
    warning = None
    if not asymptotic_valid:
        warning = (
            "Expected counts below five make the asymptotic result unreliable; "
            "use the Monte Carlo global p-value."
        )

    return FairnessResult(
        statistic=float(chi_square.statistic),
        p_value=float(chi_square.pvalue),
        degrees_of_freedom=len(wheel.labels) - 1,
        expected_counts=tuple(float(value) for value in expected),
        pearson_residuals=tuple(float(value) for value in residuals),
        cramers_v=float(
            np.sqrt(chi_square.statistic / (total * (len(wheel.labels) - 1)))
        ),
        asymptotic_valid=asymptotic_valid,
        warning=warning,
    )


def monte_carlo_global_pvalue(
    counts: ArrayLike,
    wheel: WheelSpec,
    simulations: int,
    rng: np.random.Generator,
) -> float:
    """Estimate the uniform-null global chi-square p-value with add-one correction."""

    wheel = _validated_wheel(wheel)
    values = _validated_counts(counts, len(wheel.labels))
    simulations = _validated_simulations(simulations)
    rng = _validated_rng(rng)
    total = int(values.sum())
    pocket_count = len(wheel.labels)
    expected = _uniform_expected_counts(total, pocket_count)
    observed_statistic = _pearson_statistic(values, expected)
    samples = rng.multinomial(total, np.full(pocket_count, 1 / pocket_count), size=simulations)
    simulated_statistics = np.sum((samples - expected) ** 2 / expected, axis=1)
    return float(
        (1 + np.count_nonzero(simulated_statistics >= observed_statistic))
        / (simulations + 1)
    )


def max_count_test(
    counts: ArrayLike,
    wheel: WheelSpec,
    simulations: int,
    rng: np.random.Generator,
) -> MaxCountResult:
    """Correct a hottest-pocket test for selecting that pocket after observing data."""

    wheel = _validated_wheel(wheel)
    values = _validated_counts(counts, len(wheel.labels))
    simulations = _validated_simulations(simulations)
    rng = _validated_rng(rng)
    total = int(values.sum())
    pocket_count = len(wheel.labels)
    observed_max = int(values.max())
    naive_p_value = float(
        scipy.stats.binom.sf(observed_max - 1, total, 1 / pocket_count)
    )
    simulated_maxima = rng.multinomial(
        total, np.full(pocket_count, 1 / pocket_count), size=simulations
    ).max(axis=1)
    familywise_p_value = float(
        (1 + np.count_nonzero(simulated_maxima >= observed_max)) / (simulations + 1)
    )

    return MaxCountResult(
        observed_max=observed_max,
        naive_p_value=naive_p_value,
        bonferroni_p_value=min(1.0, pocket_count * naive_p_value),
        familywise_p_value=familywise_p_value,
        simulations=simulations,
    )


def dirichlet_posterior(
    counts: ArrayLike, prior_strength: float, level: float
) -> PosteriorEstimate:
    """Return marginal Beta credible intervals for a symmetric Dirichlet posterior.

    ``prior_strength`` is the shared Dirichlet concentration assigned to every
    pocket, equivalent to that many prior pseudo-counts per pocket.
    """

    values = _validated_counts(counts)
    if isinstance(prior_strength, bool) or not isinstance(prior_strength, Real):
        raise ValueError("prior_strength must be a finite positive number.")
    prior_strength = float(prior_strength)
    if not np.isfinite(prior_strength) or prior_strength <= 0.0:
        raise ValueError("prior_strength must be a finite positive number.")
    level = _validated_probability_input(level, "level")

    posterior_parameters = values.astype(float) + prior_strength
    total_concentration = float(posterior_parameters.sum())
    posterior_means = posterior_parameters / total_concentration
    if values.size == 1:
        lower_bounds = np.ones(1, dtype=float)
        upper_bounds = np.ones(1, dtype=float)
    else:
        lower_bounds, upper_bounds = scipy.stats.beta.interval(
            level,
            posterior_parameters,
            total_concentration - posterior_parameters,
        )

    return PosteriorEstimate(
        posterior_means=tuple(float(value) for value in posterior_means),
        lower_bounds=tuple(float(value) for value in lower_bounds),
        upper_bounds=tuple(float(value) for value in upper_bounds),
        prior_strength=prior_strength,
        level=level,
    )


def split_spin_history(
    spins: ArrayLike, validation_fraction: float, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """Randomly divide one-dimensional spin history into disjoint data splits."""

    values = np.asarray(spins)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("spins must be a one-dimensional history with at least two values.")
    validation_fraction = _validated_probability_input(
        validation_fraction, "validation_fraction"
    )
    rng = _validated_rng(rng)
    validation_count = int(round(values.size * validation_fraction))
    validation_count = min(max(validation_count, 1), values.size - 1)
    validation_indices = rng.permutation(values.size)[:validation_count]
    is_validation = np.zeros(values.size, dtype=bool)
    is_validation[validation_indices] = True
    return values[~is_validation], values[is_validation]
