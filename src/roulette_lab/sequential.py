"""Sequential likelihood-ratio evidence and Page-style CUSUM diagnostics."""

from dataclasses import dataclass
from numbers import Real

import numpy as np
from numpy.typing import ArrayLike, NDArray


_MAX_FLOAT = np.finfo(float).max
_LOG_MAX_FLOAT = float(np.log(_MAX_FLOAT))
_PRE_MAX_FLOAT = np.nextafter(_MAX_FLOAT, 0.0)


@dataclass(frozen=True, slots=True)
class SequentialEvidence:
    """Likelihood-ratio evidence path for one declared null and alternative."""

    log_likelihood_ratio: NDArray[np.float64]
    e_values: NDArray[np.float64]
    threshold: float
    first_crossing: int | None
    p0: float
    p1: float
    alpha: float


@dataclass(frozen=True, slots=True)
class CUSUMResult:
    """Page-style CUSUM scores for one declared null and alternative."""

    scores: NDArray[np.float64]
    threshold: float
    first_alarm: int | None
    p0: float
    p1: float


def _binary_observations(observations: ArrayLike) -> NDArray[np.int64]:
    values = np.asarray(observations)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("observations must be a non-empty one-dimensional binary array.")
    if np.issubdtype(values.dtype, np.bool_):
        return values.astype(np.int64)
    if not np.issubdtype(values.dtype, np.number) or np.issubdtype(
        values.dtype, np.complexfloating
    ):
        raise ValueError("observations must be a non-empty one-dimensional binary array.")
    if not np.all(np.isfinite(values)) or np.any((values != 0) & (values != 1)):
        raise ValueError("observations must be a non-empty one-dimensional binary array.")
    return values.astype(np.int64)


def _open_unit(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number strictly between zero and one.")
    value = float(value)
    if not np.isfinite(value) or not 0.0 < value < 1.0:
        raise ValueError(f"{name} must be a finite number strictly between zero and one.")
    return value


def _ordered_probabilities(p0: float, p1: float) -> tuple[float, float]:
    p0 = _open_unit(p0, "p0")
    p1 = _open_unit(p1, "p1")
    if p1 <= p0:
        raise ValueError("p1 must be strictly greater than p0.")
    return p0, p1


def _positive_finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a positive finite number.")
    value = float(value)
    if not np.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be a positive finite number.")
    return value


def _log_likelihood_increments(
    values: NDArray[np.int64], p0: float, p1: float
) -> NDArray[np.float64]:
    hit_increment = np.log(p1) - np.log(p0)
    miss_increment = np.log1p(-p1) - np.log1p(-p0)
    return np.where(values == 1, hit_increment, miss_increment)


def likelihood_ratio_path(
    observations: ArrayLike, p0: float, p1: float, alpha: float
) -> SequentialEvidence:
    """Compute a simple-null versus simple-alternative likelihood-ratio path.

    The returned e-values meet the declared simple-null/simple-alternative
    contract; they do not establish unrestricted optional-stopping validity.
    Thresholds are representationally capped at the largest finite float when
    ``alpha`` is below the reciprocal range of that float. Crossing detection
    always uses the uncapped log-likelihood path and ``-log(alpha)``.
    In that extreme range, displayed pre-crossing e-values that would overflow
    use the next float below the cap; values at and after the true crossing use
    the cap itself, so the displayed crossing agrees with ``first_crossing``.
    """

    values = _binary_observations(observations)
    p0, p1 = _ordered_probabilities(p0, p1)
    alpha = _open_unit(alpha, "alpha")
    increments = _log_likelihood_increments(values, p0, p1)
    log_path = np.cumsum(increments, dtype=float)
    e_values = np.exp(np.minimum(log_path, _LOG_MAX_FLOAT))
    log_threshold = float(-np.log(alpha))
    if log_threshold > _LOG_MAX_FLOAT:
        threshold = _MAX_FLOAT
        e_values[log_path >= _LOG_MAX_FLOAT] = _PRE_MAX_FLOAT
        e_values[log_path >= log_threshold] = _MAX_FLOAT
    else:
        threshold = float(np.exp(log_threshold))
        e_values[log_path >= _LOG_MAX_FLOAT] = _MAX_FLOAT
    crossings = np.flatnonzero(log_path >= log_threshold)
    first_crossing = int(crossings[0] + 1) if crossings.size else None
    return SequentialEvidence(
        log_likelihood_ratio=log_path,
        e_values=e_values,
        threshold=threshold,
        first_crossing=first_crossing,
        p0=p0,
        p1=p1,
        alpha=alpha,
    )


def cusum_change_detection(
    observations: ArrayLike, p0: float, p1: float, threshold: float
) -> CUSUMResult:
    """Compute Page-style CUSUM scores for a declared upward probability change."""

    values = _binary_observations(observations)
    p0, p1 = _ordered_probabilities(p0, p1)
    threshold = _positive_finite(threshold, "threshold")
    increments = _log_likelihood_increments(values, p0, p1)
    scores = np.empty(values.size, dtype=float)
    running = 0.0
    for index, increment in enumerate(increments):
        running = max(0.0, running + float(increment))
        scores[index] = running
    alarms = np.flatnonzero(scores >= threshold)
    first_alarm = int(alarms[0] + 1) if alarms.size else None
    return CUSUMResult(
        scores=scores,
        threshold=threshold,
        first_alarm=first_alarm,
        p0=p0,
        p1=p1,
    )
