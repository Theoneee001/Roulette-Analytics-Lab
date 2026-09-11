"""Typed roulette bets, exact returns, special rules, and Kelly sizing."""

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .wheels import WheelKind, WheelSpec


class BetKind(str, Enum):
    STRAIGHT = "straight"
    SPLIT = "split"
    STREET = "street"
    CORNER = "corner"
    SIX_LINE = "six_line"
    DOZEN = "dozen"
    COLUMN = "column"
    RED = "red"
    BLACK = "black"
    EVEN = "even"
    ODD = "odd"
    LOW = "low"
    HIGH = "high"


class SpecialRule(str, Enum):
    STANDARD = "standard"
    LA_PARTAGE = "la_partage"
    EN_PRISON = "en_prison"


class EnPrisonState(str, Enum):
    ACTIVE = "active"
    IMPRISONED = "imprisoned"


_PAYOUTS = {
    BetKind.STRAIGHT: 35,
    BetKind.SPLIT: 17,
    BetKind.STREET: 11,
    BetKind.CORNER: 8,
    BetKind.SIX_LINE: 5,
    BetKind.DOZEN: 2,
    BetKind.COLUMN: 2,
    BetKind.RED: 1,
    BetKind.BLACK: 1,
    BetKind.EVEN: 1,
    BetKind.ODD: 1,
    BetKind.LOW: 1,
    BetKind.HIGH: 1,
}

_COVERAGE_SIZES = {
    BetKind.STRAIGHT: 1,
    BetKind.SPLIT: 2,
    BetKind.STREET: 3,
    BetKind.CORNER: 4,
    BetKind.SIX_LINE: 6,
    BetKind.DOZEN: 12,
    BetKind.COLUMN: 12,
    BetKind.RED: 18,
    BetKind.BLACK: 18,
    BetKind.EVEN: 18,
    BetKind.ODD: 18,
    BetKind.LOW: 18,
    BetKind.HIGH: 18,
}

_OUTSIDE_BETS = frozenset(
    {
        BetKind.RED,
        BetKind.BLACK,
        BetKind.EVEN,
        BetKind.ODD,
        BetKind.LOW,
        BetKind.HIGH,
    }
)


@dataclass(frozen=True, slots=True)
class BetSpec:
    """A standard roulette bet with fixed coverage and net payout odds."""

    kind: BetKind
    covered_labels: tuple[str, ...]
    net_odds: int

    def __post_init__(self) -> None:
        kind = BetKind(self.kind)
        labels = tuple(self.covered_labels)
        if len(labels) != _COVERAGE_SIZES[kind]:
            raise ValueError(
                f"{kind.value} requires {_COVERAGE_SIZES[kind]} labels."
            )
        if len(set(labels)) != len(labels):
            raise ValueError("Bet coverage labels must be unique.")
        if self.net_odds != _PAYOUTS[kind]:
            raise ValueError(f"{kind.value} bets have fixed net odds of {_PAYOUTS[kind]}.")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "covered_labels", labels)


def make_standard_bet(
    kind: BetKind, selection: tuple[str, ...], wheel: WheelSpec
) -> BetSpec:
    """Build a standard bet after validating its covered numbered pockets."""
    kind = BetKind(kind)
    selection = tuple(selection)
    if kind in _OUTSIDE_BETS:
        if selection:
            raise ValueError(f"{kind.value} bets do not take a label selection.")
        covered_labels = _outside_coverage(kind, wheel)
    else:
        required_size = _COVERAGE_SIZES[kind]
        if len(selection) != required_size:
            raise ValueError(f"{kind.value} requires {required_size} labels.")
        covered_labels = selection

    _validate_numbered_coverage(covered_labels, wheel)
    return BetSpec(kind=kind, covered_labels=covered_labels, net_odds=_PAYOUTS[kind])


def expected_net_return(
    wheel: WheelSpec, bet: BetSpec, rule: SpecialRule
) -> float:
    """Return expected profit or loss per one-unit initial stake."""
    rule = SpecialRule(rule)
    probabilities = _probabilities_for_bet(wheel, bet)
    win_probability = sum(probabilities[label] for label in bet.covered_labels)
    zero_probability = sum(
        probability for label, probability in probabilities.items() if label in {"0", "00"}
    )

    if rule is SpecialRule.STANDARD:
        return win_probability * bet.net_odds - (1 - win_probability)

    _validate_european_even_money_rule(wheel, bet, rule)
    if rule is SpecialRule.LA_PARTAGE:
        non_zero_loss_probability = 1 - win_probability - zero_probability
        return (
            win_probability * bet.net_odds
            - non_zero_loss_probability
            - 0.5 * zero_probability
        )
    return _en_prison_expected_return(
        win_probability, zero_probability, EnPrisonState.ACTIVE
    )


def house_edge(wheel: WheelSpec, bet: BetSpec, rule: SpecialRule) -> float:
    """Return the casino advantage per unit staked."""
    return -expected_net_return(wheel, bet, rule)


def kelly_fraction(probability: float, net_odds: float, fraction: float = 1.0) -> float:
    """Return a capped full or fractional Kelly allocation."""
    if not isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError("Probability must be between zero and one.")
    if not isfinite(net_odds) or net_odds <= 0:
        raise ValueError("Net odds must be positive.")
    if not isfinite(fraction) or not 0 <= fraction <= 1:
        raise ValueError("Kelly fraction must be between zero and one.")

    full_kelly = (probability * net_odds - (1 - probability)) / net_odds
    full_kelly = min(1.0, max(0.0, full_kelly))
    return full_kelly * fraction


def _outside_coverage(kind: BetKind, wheel: WheelSpec) -> tuple[str, ...]:
    numbered_labels = tuple(label for label in wheel.labels if label not in {"0", "00"})
    if kind is BetKind.RED:
        return tuple(
            label
            for label, colour in zip(wheel.labels, wheel.colours)
            if colour == "red"
        )
    if kind is BetKind.BLACK:
        return tuple(
            label
            for label, colour in zip(wheel.labels, wheel.colours)
            if colour == "black"
        )
    numbers = tuple(int(label) for label in numbered_labels)
    if kind is BetKind.EVEN:
        return tuple(str(number) for number in numbers if number % 2 == 0)
    if kind is BetKind.ODD:
        return tuple(str(number) for number in numbers if number % 2 == 1)
    if kind is BetKind.LOW:
        return tuple(str(number) for number in numbers if number <= 18)
    return tuple(str(number) for number in numbers if number >= 19)


def _validate_numbered_coverage(labels: tuple[str, ...], wheel: WheelSpec) -> None:
    if len(set(labels)) != len(labels):
        raise ValueError("Bet coverage labels must be unique.")
    numbered_pockets = set(wheel.labels) - {"0", "00"}
    invalid_labels = set(labels) - numbered_pockets
    if invalid_labels:
        raise ValueError("Bet coverage must contain only numbered pocket labels.")


def _probabilities_for_bet(wheel: WheelSpec, bet: BetSpec) -> dict[str, float]:
    labels = set(bet.covered_labels)
    missing_labels = labels - set(wheel.labels)
    if missing_labels:
        raise ValueError("Bet coverage contains labels not present on the wheel.")
    return {
        label: float(probability)
        for label, probability in zip(wheel.labels, wheel.probabilities)
    }


def _validate_european_even_money_rule(
    wheel: WheelSpec, bet: BetSpec, rule: SpecialRule
) -> None:
    if wheel.kind is not WheelKind.EUROPEAN or bet.net_odds != 1:
        raise ValueError(f"{rule.value} requires a European even-money bet.")


def _en_prison_expected_return(
    win_probability: float, zero_probability: float, state: EnPrisonState
) -> float:
    non_zero_loss_probability = 1 - win_probability - zero_probability
    if state is EnPrisonState.ACTIVE:
        return (
            win_probability
            - non_zero_loss_probability
            + zero_probability
            * _en_prison_expected_return(
                win_probability, zero_probability, EnPrisonState.IMPRISONED
            )
        )

    # A zero while imprisoned leaves the stake imprisoned, creating this loop.
    return -non_zero_loss_probability / (1 - zero_probability)
