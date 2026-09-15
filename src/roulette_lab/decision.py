"""Posterior edge summaries for clearly labelled heuristic stake sizing.

The lower-posterior-quantile Kelly output is a conservative heuristic. It is
not a theorem, a profit guarantee, or personalised gambling advice.
"""

from dataclasses import dataclass
from numbers import Integral, Real

import numpy as np
import scipy.stats

from .bets import kelly_fraction


_MAX_SCIPY_FUTURE_TRIALS = int(np.iinfo(np.intp).max)


@dataclass(frozen=True, slots=True)
class PosteriorEdgeSummary:
    """Beta-posterior edge estimates and a heuristic Kelly stake comparison.

    ``quantile_kelly`` applies Kelly sizing to a lower posterior quantile as a
    conservative heuristic; it does not guarantee a positive outcome.
    """

    posterior_alpha: float
    posterior_beta: float
    posterior_mean: float
    credible_interval: tuple[float, float]
    break_even_probability: float
    probability_positive_edge: float
    expected_net_return: float
    plugin_kelly: float
    quantile_probability: float
    quantile_kelly: float
    predictive_interval: tuple[int, int]


def posterior_edge_summary(
    hits: int,
    trials: int,
    prior_alpha: float,
    prior_beta: float,
    net_odds: float,
    level: float,
    lower_quantile: float,
    future_trials: int,
) -> PosteriorEdgeSummary:
    """Summarize a Beta-Binomial posterior and heuristic Kelly allocations.

    The plug-in allocation uses the posterior mean. The lower-quantile
    allocation is deliberately labelled a heuristic rather than a guarantee.
    """

    hits, trials = _validated_counts(hits, trials)
    prior_alpha = _positive_finite(prior_alpha, "prior_alpha")
    prior_beta = _positive_finite(prior_beta, "prior_beta")
    net_odds = _positive_finite(net_odds, "net_odds")
    level = _open_unit(level, "level")
    lower_quantile = _open_unit(lower_quantile, "lower_quantile")
    future_trials = _scipy_trial_count(future_trials, "future_trials")

    posterior_alpha, posterior_beta, posterior_shape_sum = _posterior_shapes(
        hits, trials, prior_alpha, prior_beta
    )
    posterior_mean = posterior_alpha / posterior_shape_sum
    credible_interval = scipy.stats.beta.interval(level, posterior_alpha, posterior_beta)
    break_even_probability = 1.0 / (net_odds + 1.0)
    probability_positive_edge = scipy.stats.beta.sf(
        break_even_probability, posterior_alpha, posterior_beta
    )
    quantile_probability = scipy.stats.beta.ppf(
        lower_quantile, posterior_alpha, posterior_beta
    )
    predictive_interval = scipy.stats.betabinom.interval(
        level, future_trials, posterior_alpha, posterior_beta
    )

    return PosteriorEdgeSummary(
        posterior_alpha=posterior_alpha,
        posterior_beta=posterior_beta,
        posterior_mean=float(posterior_mean),
        credible_interval=tuple(map(float, credible_interval)),
        break_even_probability=break_even_probability,
        probability_positive_edge=float(probability_positive_edge),
        expected_net_return=float(posterior_mean * net_odds - (1.0 - posterior_mean)),
        plugin_kelly=kelly_fraction(float(posterior_mean), net_odds),
        quantile_probability=float(quantile_probability),
        quantile_kelly=kelly_fraction(float(quantile_probability), net_odds),
        predictive_interval=tuple(int(value) for value in predictive_interval),
    )


def _validated_counts(hits: object, trials: object) -> tuple[int, int]:
    trials = _nonnegative_integer(trials, "trials")
    hits = _nonnegative_integer(hits, "hits")
    if hits > trials:
        raise ValueError("hits must not exceed trials.")
    return hits, trials


def _nonnegative_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 0:
        raise ValueError(f"{name} must be a non-negative integer.")
    return int(value)


def _scipy_trial_count(value: object, name: str) -> int:
    count = _nonnegative_integer(value, name)
    if count > _MAX_SCIPY_FUTURE_TRIALS:
        raise ValueError(
            f"{name} must be at most {_MAX_SCIPY_FUTURE_TRIALS} "
            "for SciPy's integer range."
        )
    return count


def _posterior_shapes(
    hits: int, trials: int, prior_alpha: float, prior_beta: float
) -> tuple[float, float, float]:
    try:
        prior_shape_sum = prior_alpha + prior_beta
        posterior_alpha = prior_alpha + hits
        posterior_beta = prior_beta + trials - hits
        posterior_shape_sum = posterior_alpha + posterior_beta
    except OverflowError as error:
        raise ValueError("Prior and posterior shape sums must be finite.") from error
    if not all(
        np.isfinite(value)
        for value in (
            prior_shape_sum,
            posterior_alpha,
            posterior_beta,
            posterior_shape_sum,
        )
    ):
        raise ValueError("Prior and posterior shape sums must be finite.")
    return posterior_alpha, posterior_beta, posterior_shape_sum


def _positive_finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a positive finite number.")
    value = float(value)
    if not np.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be a positive finite number.")
    return value


def _open_unit(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be strictly between zero and one.")
    value = float(value)
    if not np.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError(f"{name} must be strictly between zero and one.")
    return value
