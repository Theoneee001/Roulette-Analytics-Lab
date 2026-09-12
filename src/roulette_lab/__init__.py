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
from .statistics import (
    FairnessResult,
    MaxCountResult,
    PosteriorEstimate,
    chi_square_fairness,
    dirichlet_posterior,
    max_count_test,
    monte_carlo_global_pvalue,
    split_spin_history,
)

__all__ = [
    "BetKind",
    "BetSpec",
    "EnPrisonState",
    "FairnessResult",
    "MaxCountResult",
    "Pocket",
    "PosteriorEstimate",
    "SpecialRule",
    "WheelKind",
    "WheelSpec",
    "expected_net_return",
    "house_edge",
    "kelly_fraction",
    "chi_square_fairness",
    "dirichlet_posterior",
    "make_biased_wheel",
    "make_fair_wheel",
    "make_standard_bet",
    "max_count_test",
    "monte_carlo_global_pvalue",
    "split_spin_history",
    "validate_probability_vector",
]
