"""Validated models and analyses for the Roulette Analytics Lab."""

from .bets import (
    BetKind,
    BetSpec,
    EnPrisonState,
    SpecialRule,
    expected_net_return,
    house_edge,
    kelly_fraction,
    make_standard_bet,
)
from .wheels import (
    Pocket,
    WheelKind,
    WheelSpec,
    make_biased_wheel,
    make_fair_wheel,
    validate_probability_vector,
)

__all__ = [
    "BetKind",
    "BetSpec",
    "EnPrisonState",
    "Pocket",
    "SpecialRule",
    "WheelKind",
    "WheelSpec",
    "expected_net_return",
    "house_edge",
    "kelly_fraction",
    "make_biased_wheel",
    "make_fair_wheel",
    "make_standard_bet",
    "validate_probability_vector",
]
