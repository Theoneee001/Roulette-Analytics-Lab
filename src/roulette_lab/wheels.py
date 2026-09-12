"""Roulette wheel labels, colours, and probability specifications."""

from dataclasses import dataclass
from enum import Enum
from numbers import Real

import numpy as np
from numpy.typing import ArrayLike


class WheelKind(str, Enum):
    EUROPEAN = "european"
    AMERICAN = "american"


@dataclass(frozen=True, slots=True)
class Pocket:
    """A labelled roulette pocket and its display colour."""

    label: str
    colour: str


@dataclass(frozen=True, slots=True)
class WheelSpec:
    kind: WheelKind
    labels: tuple[str, ...]
    colours: tuple[str, ...]
    probabilities: np.ndarray

    def __post_init__(self) -> None:
        kind = WheelKind(self.kind)
        labels = tuple(self.labels)
        colours = tuple(self.colours)
        if len(labels) != len(colours):
            raise ValueError("Wheel labels and colours must have the same size.")
        if len(set(labels)) != len(labels):
            raise ValueError("Wheel labels must be unique.")

        probabilities = validate_probability_vector(
            np.array(self.probabilities, dtype=float, copy=True), len(labels)
        )
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "labels", labels)
        object.__setattr__(self, "colours", colours)
        object.__setattr__(self, "probabilities", probabilities)

    @property
    def pockets(self) -> tuple[Pocket, ...]:
        return tuple(
            Pocket(label=label, colour=colour)
            for label, colour in zip(self.labels, self.colours)
        )


_RED_NUMBERS = frozenset(
    {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
)


def validate_probability_vector(probabilities: ArrayLike, size: int) -> np.ndarray:
    values = np.asarray(probabilities, dtype=float)
    if values.shape != (size,):
        raise ValueError(f"Expected {size} pocket probabilities.")
    if np.any(~np.isfinite(values)) or np.any(values < 0):
        raise ValueError("Pocket probabilities must be finite and non-negative.")
    if not np.isclose(values.sum(), 1.0, rtol=0.0, atol=1e-12):
        raise ValueError("Pocket probabilities must sum to one.")
    values.setflags(write=False)
    return values


def _pockets_for(kind: WheelKind) -> tuple[Pocket, ...]:
    kind = WheelKind(kind)
    zero_labels = ("0",) if kind is WheelKind.EUROPEAN else ("0", "00")
    labels = zero_labels + tuple(str(number) for number in range(1, 37))
    colours = tuple(
        "green" if label in {"0", "00"} else
        "red" if int(label) in _RED_NUMBERS else "black"
        for label in labels
    )
    return tuple(Pocket(label=label, colour=colour) for label, colour in zip(labels, colours))


def make_fair_wheel(kind: WheelKind) -> WheelSpec:
    pockets = _pockets_for(kind)
    probabilities = np.full(len(pockets), 1 / len(pockets), dtype=float)
    return WheelSpec(
        kind=WheelKind(kind),
        labels=tuple(pocket.label for pocket in pockets),
        colours=tuple(pocket.colour for pocket in pockets),
        probabilities=probabilities,
    )


def make_biased_wheel(kind: WheelKind, probabilities: ArrayLike) -> WheelSpec:
    pockets = _pockets_for(kind)
    validated = validate_probability_vector(
        np.array(probabilities, dtype=float, copy=True), len(pockets)
    )
    return WheelSpec(
        kind=WheelKind(kind),
        labels=tuple(pocket.label for pocket in pockets),
        colours=tuple(pocket.colour for pocket in pockets),
        probabilities=validated,
    )


def wheel_with_single_pocket_probability(
    base_wheel: WheelSpec, label: str, probability: float
) -> WheelSpec:
    """Set one pocket probability while preserving every other relative weight."""

    if not isinstance(base_wheel, WheelSpec):
        raise TypeError("base_wheel must be a WheelSpec.")
    if not isinstance(label, str) or label not in base_wheel.labels:
        raise ValueError("label must identify a pocket on base_wheel.")
    if isinstance(probability, bool) or not isinstance(probability, Real):
        raise ValueError("probability must be a finite number strictly between zero and one.")
    probability = float(probability)
    if not np.isfinite(probability) or not 0.0 < probability < 1.0:
        raise ValueError("probability must be a finite number strictly between zero and one.")

    target_index = base_wheel.labels.index(label)
    other_probabilities = np.delete(base_wheel.probabilities, target_index)
    other_mass = float(other_probabilities.sum())
    if other_mass <= 0.0:
        raise ValueError("Cannot redistribute a wheel with no probability outside label.")

    adjusted = np.array(base_wheel.probabilities, dtype=float, copy=True)
    adjusted[target_index] = probability
    adjusted[np.arange(len(adjusted)) != target_index] *= (1.0 - probability) / other_mass
    return WheelSpec(
        kind=base_wheel.kind,
        labels=base_wheel.labels,
        colours=base_wheel.colours,
        probabilities=adjusted,
    )
