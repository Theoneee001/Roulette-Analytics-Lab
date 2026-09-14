"""Tail-risk summaries and common-random-number Kelly risk frontiers."""

from dataclasses import replace
from numbers import Integral, Real

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

from .bankroll import (
    BankrollConfig,
    StrategyKind,
    simulate_bankroll,
    summarize_bankroll,
)
from .bets import BetSpec, SpecialRule
from .wheels import WheelSpec


_FRACTION_STRATEGIES = {
    0.25: StrategyKind.QUARTER_KELLY,
    0.5: StrategyKind.HALF_KELLY,
    1.0: StrategyKind.FULL_KELLY,
}


def conditional_value_at_risk(
    losses: ArrayLike, tail_probability: float = 0.05
) -> float:
    """Return the mean of the largest losses in the requested upper tail.

    Values use a loss convention: larger values are worse. In bankroll
    reporting, the input is the non-negative terminal shortfall
    ``max(initial_bankroll - terminal_equity, 0)``.
    """

    values = _finite_vector(losses, "losses")
    tail_probability = _open_unit(tail_probability, "tail_probability")
    count = max(1, int(np.ceil(values.size * tail_probability)))
    return float(np.mean(np.sort(values)[-count:]))


def build_risk_frontier(
    base_config: BankrollConfig,
    wheel: WheelSpec,
    bet: BetSpec,
    rule: SpecialRule,
    fractions: ArrayLike,
    seed: int,
) -> pd.DataFrame:
    """Compare quarter, half, and full Kelly with common random outcomes.

    Each accepted fraction creates a fresh generator from the same ``seed``.
    This common-random-number design makes strategy differences reflect stake
    sizing rather than different simulated pocket sequences.
    """

    if not isinstance(base_config, BankrollConfig):
        raise TypeError("base_config must be a BankrollConfig.")
    if not isinstance(wheel, WheelSpec):
        raise TypeError("wheel must be a WheelSpec.")
    if not isinstance(bet, BetSpec):
        raise TypeError("bet must be a BetSpec.")
    rule = SpecialRule(rule)
    seed = _nonnegative_integer(seed, "seed")
    fractions = _validated_fractions(fractions)
    estimated_probability = _estimated_probability(base_config, wheel, bet)

    rows = []
    for fraction in fractions:
        config = replace(
            base_config,
            strategy=_FRACTION_STRATEGIES[fraction],
            estimated_win_probability=estimated_probability,
        )
        simulation = simulate_bankroll(
            config, wheel, bet, rule, np.random.default_rng(seed)
        )
        summary = summarize_bankroll(simulation)
        terminal_equity = simulation.equity_paths[:, -1]
        shortfalls = np.maximum(config.initial_bankroll - terminal_equity, 0.0)
        with np.errstate(divide="ignore"):
            expected_log_growth = float(
                np.mean(np.log(terminal_equity / config.initial_bankroll))
            )
        rows.append(
            {
                "kelly_fraction_multiplier": fraction,
                "strategy": config.strategy.value,
                "terminal_mean": summary.terminal_mean,
                "terminal_median": summary.terminal_median,
                "probability_of_loss": summary.probability_of_loss,
                "expected_maximum_drawdown": summary.expected_maximum_drawdown,
                "expected_log_growth": expected_log_growth,
                "terminal_cvar_shortfall": conditional_value_at_risk(shortfalls),
            }
        )
    return pd.DataFrame(rows)


def _finite_vector(values: ArrayLike, name: str) -> NDArray[np.float64]:
    try:
        values = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a non-empty finite one-dimensional array.") from error
    if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError(f"{name} must be a non-empty finite one-dimensional array.")
    return values


def _open_unit(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be strictly between zero and one.")
    value = float(value)
    if not np.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError(f"{name} must be strictly between zero and one.")
    return value


def _nonnegative_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 0:
        raise ValueError(f"{name} must be a non-negative integer.")
    return int(value)


def _validated_fractions(fractions: ArrayLike) -> tuple[float, ...]:
    values = _finite_vector(fractions, "fractions")
    normalized = tuple(sorted(float(value) for value in values))
    if any(value not in _FRACTION_STRATEGIES for value in normalized):
        raise ValueError("fractions must contain only 0.25, 0.5, and 1.0.")
    if len(set(normalized)) != len(normalized):
        raise ValueError("fractions must not contain duplicates.")
    return normalized


def _estimated_probability(
    base_config: BankrollConfig, wheel: WheelSpec, bet: BetSpec
) -> float:
    if base_config.estimated_win_probability is not None:
        return base_config.estimated_win_probability
    return float(
        sum(
            probability
            for label, probability in zip(wheel.labels, wheel.probabilities, strict=True)
            if label in bet.covered_labels
        )
    )
