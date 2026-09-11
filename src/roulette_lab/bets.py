"""Typed roulette bets, exact returns, special rules, and Kelly sizing."""

from dataclasses import dataclass
from enum import Enum
from math import isclose, isfinite

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

    bet = BetSpec(kind=kind, covered_labels=covered_labels, net_odds=_PAYOUTS[kind])
    _validate_bet_for_wheel(wheel, bet)
    return bet


def expected_net_return(
    wheel: WheelSpec, bet: BetSpec, rule: SpecialRule
) -> float:
    """Return expected profit or loss per one-unit initial stake."""
    rule = SpecialRule(rule)
    _validate_bet_for_wheel(wheel, bet)
    probabilities = {
        label: float(probability)
        for label, probability in zip(wheel.labels, wheel.probabilities)
    }
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


def _validate_bet_for_wheel(wheel: WheelSpec, bet: BetSpec) -> None:
    labels = frozenset(bet.covered_labels)
    if bet.kind is BetKind.STRAIGHT:
        if labels - set(wheel.labels):
            raise ValueError("Straight bet labels must be present on the wheel.")
        return

    if bet.kind in _OUTSIDE_BETS:
        if labels != frozenset(_outside_coverage(bet.kind, wheel)):
            raise ValueError(f"{bet.kind.value} coverage must match the standard wheel coverage.")
        return

    numbered_labels = frozenset(str(number) for number in range(1, 37))
    if not labels <= numbered_labels or not labels <= set(wheel.labels):
        raise ValueError(
            "Non-straight inside bets must contain labels 1 through 36 present on the wheel."
        )
    numbers = frozenset(int(label) for label in labels)
    if not _is_canonical_geometry(bet.kind, numbers):
        raise ValueError(f"Bet coverage does not form a valid {bet.kind.value} geometry.")


def _is_canonical_geometry(kind: BetKind, numbers: frozenset[int]) -> bool:
    if kind is BetKind.SPLIT:
        first, second = sorted(numbers)
        same_row = (first - 1) // 3 == (second - 1) // 3 and second - first == 1
        same_column = first % 3 == second % 3 and second - first == 3
        return same_row or same_column
    if kind is BetKind.STREET:
        row = (min(numbers) - 1) // 3
        return numbers == frozenset(range(3 * row + 1, 3 * row + 4))
    if kind is BetKind.CORNER:
        rows = {(number - 1) // 3 for number in numbers}
        columns = {(number - 1) % 3 for number in numbers}
        return (
            len(rows) == 2
            and len(columns) == 2
            and max(rows) - min(rows) == 1
            and max(columns) - min(columns) == 1
            and numbers
            == frozenset(3 * row + column + 1 for row in rows for column in columns)
        )
    if kind is BetKind.SIX_LINE:
        rows = {(number - 1) // 3 for number in numbers}
        return len(rows) == 2 and max(rows) - min(rows) == 1
    if kind is BetKind.DOZEN:
        return numbers in {
            frozenset(range(1, 13)),
            frozenset(range(13, 25)),
            frozenset(range(25, 37)),
        }
    if kind is BetKind.COLUMN:
        return numbers in {
            frozenset(range(1, 37, 3)),
            frozenset(range(2, 37, 3)),
            frozenset(range(3, 37, 3)),
        }
    return False


def _validate_european_even_money_rule(
    wheel: WheelSpec, bet: BetSpec, rule: SpecialRule
) -> None:
    if wheel.kind is not WheelKind.EUROPEAN or bet.net_odds != 1:
        raise ValueError(f"{rule.value} requires a European even-money bet.")


def _en_prison_expected_return(
    win_probability: float, zero_probability: float, state: EnPrisonState
) -> float:
    if isclose(zero_probability, 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("En Prison stake never settles when zero has all probability mass.")
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
