"""Seeded bankroll simulations and path-level roulette risk metrics.

Kelly sizing is a conditional expected-log-growth calculation under the
configured probability and selected payout. It does not guarantee profit.
"""

from dataclasses import dataclass
from enum import Enum
from numbers import Integral, Real

import numpy as np

from .bets import BetSpec, SpecialRule, expected_net_return, kelly_fraction
from .wheels import WheelSpec


class StrategyKind(str, Enum):
    """Supported stake-sizing strategies.

    ``KELLY`` remains an alias for full Kelly to match the first simulator
    interface while giving downstream tables an explicit ``full_kelly`` name.
    """

    FLAT = "flat"
    MARTINGALE = "martingale"
    REVERSE_MARTINGALE = "reverse_martingale"
    FULL_KELLY = "full_kelly"
    KELLY = "full_kelly"
    HALF_KELLY = "half_kelly"
    QUARTER_KELLY = "quarter_kelly"


_KELLY_STRATEGIES = frozenset(
    {
        StrategyKind.FULL_KELLY,
        StrategyKind.HALF_KELLY,
        StrategyKind.QUARTER_KELLY,
    }
)
_KELLY_MULTIPLIERS = {
    StrategyKind.FULL_KELLY: 1.0,
    StrategyKind.HALF_KELLY: 0.5,
    StrategyKind.QUARTER_KELLY: 0.25,
}


@dataclass(frozen=True, slots=True)
class BankrollConfig:
    """Validated immutable controls for a single strategy simulation.

    Every requested stake is rounded *down* to an exact multiple of
    ``min_chip`` after bankroll and table caps are applied. Rounding down is
    deterministic and ensures those caps are never exceeded.
    """

    initial_bankroll: float
    base_stake: float
    spins: int
    paths: int
    strategy: StrategyKind
    estimated_win_probability: float | None = None
    min_chip: float = 1.0
    table_limit: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    custom_net_odds: float | None = None

    def __post_init__(self) -> None:
        initial_bankroll = _positive_number(self.initial_bankroll, "initial_bankroll")
        base_stake = _positive_number(self.base_stake, "base_stake")
        spins = _positive_integer(self.spins, "spins")
        paths = _positive_integer(self.paths, "paths")
        min_chip = _positive_number(self.min_chip, "min_chip")
        strategy = StrategyKind(self.strategy)

        if initial_bankroll < min_chip:
            raise ValueError("initial_bankroll must afford at least one min_chip.")
        if base_stake < min_chip:
            raise ValueError("base_stake must be at least min_chip.")

        table_limit = _optional_positive_number(self.table_limit, "table_limit")
        if table_limit is not None:
            if table_limit < min_chip:
                raise ValueError("table_limit must be at least min_chip.")
            if strategy not in _KELLY_STRATEGIES and base_stake > table_limit:
                raise ValueError("base_stake must not exceed table_limit.")

        stop_loss = _optional_nonnegative_number(self.stop_loss, "stop_loss")
        if stop_loss is not None and stop_loss >= initial_bankroll:
            raise ValueError("stop_loss must be below initial_bankroll.")
        take_profit = _optional_positive_number(self.take_profit, "take_profit")
        if take_profit is not None and take_profit <= initial_bankroll:
            raise ValueError("take_profit must be above initial_bankroll.")

        custom_net_odds = _optional_positive_number(self.custom_net_odds, "custom_net_odds")
        estimated_probability = self.estimated_win_probability
        if strategy in _KELLY_STRATEGIES:
            if estimated_probability is None:
                raise ValueError("estimated_win_probability is required for Kelly strategies.")
            estimated_probability = _unit_probability(
                estimated_probability, "estimated_win_probability"
            )
        elif estimated_probability is not None:
            estimated_probability = _unit_probability(
                estimated_probability, "estimated_win_probability"
            )

        object.__setattr__(self, "initial_bankroll", initial_bankroll)
        object.__setattr__(self, "base_stake", base_stake)
        object.__setattr__(self, "spins", spins)
        object.__setattr__(self, "paths", paths)
        object.__setattr__(self, "strategy", strategy)
        object.__setattr__(self, "estimated_win_probability", estimated_probability)
        object.__setattr__(self, "min_chip", min_chip)
        object.__setattr__(self, "table_limit", table_limit)
        object.__setattr__(self, "stop_loss", stop_loss)
        object.__setattr__(self, "take_profit", take_profit)
        object.__setattr__(self, "custom_net_odds", custom_net_odds)


@dataclass(frozen=True, slots=True, eq=False)
class BankrollSimulation:
    """Immutable cash, equity, and unresolved-stake paths for a simulation.

    ``paths`` is liquid cash. For an active En Prison wager, ``equity_paths``
    marks that cash plus the stake's conditional recovery value; it equals
    liquid cash for every other state and rule.
    """

    config: BankrollConfig
    paths: np.ndarray
    payout_label: str
    equity_paths: np.ndarray | None = None
    unresolved_stakes: np.ndarray | None = None

    __hash__ = None

    def __post_init__(self) -> None:
        if not isinstance(self.config, BankrollConfig):
            raise TypeError("config must be a BankrollConfig.")
        values = _validated_path_matrix(self.paths, self.config, "paths")
        equity_values = _validated_path_matrix(
            values if self.equity_paths is None else self.equity_paths,
            self.config,
            "equity_paths",
        )
        unresolved_values = _validated_unresolved_stakes(
            self.unresolved_stakes, self.config
        )
        if not np.all(equity_values[:, 0] == self.config.initial_bankroll):
            raise ValueError("equity_paths must include initial_bankroll in column zero.")
        if not isinstance(self.payout_label, str) or not self.payout_label:
            raise ValueError("payout_label must be a non-empty string.")
        object.__setattr__(self, "paths", values)
        object.__setattr__(self, "equity_paths", equity_values)
        object.__setattr__(self, "unresolved_stakes", unresolved_values)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BankrollSimulation):
            return NotImplemented
        return (
            self.config == other.config
            and self.payout_label == other.payout_label
            and np.array_equal(self.paths, other.paths)
            and np.array_equal(self.equity_paths, other.equity_paths)
            and np.array_equal(self.unresolved_stakes, other.unresolved_stakes)
        )


def _validated_path_matrix(
    values: np.ndarray, config: BankrollConfig, name: str
) -> np.ndarray:
    values = np.array(values, dtype=float, copy=True)
    expected_shape = (config.paths, config.spins + 1)
    if values.shape != expected_shape:
        raise ValueError(f"{name} must have shape {expected_shape}.")
    if not np.all(np.isfinite(values)) or np.any(values < 0.0):
        raise ValueError(f"{name} must contain finite non-negative bankrolls.")
    if not np.all(values[:, 0] == config.initial_bankroll):
        raise ValueError(f"{name} must include initial_bankroll in column zero.")
    values.setflags(write=False)
    return values


def _validated_unresolved_stakes(
    values: np.ndarray | None, config: BankrollConfig
) -> np.ndarray:
    unresolved = np.zeros(config.paths, dtype=float) if values is None else np.array(
        values, dtype=float, copy=True
    )
    if unresolved.shape != (config.paths,):
        raise ValueError(f"unresolved_stakes must have shape {(config.paths,)}.")
    if not np.all(np.isfinite(unresolved)) or np.any(unresolved < 0.0):
        raise ValueError("unresolved_stakes must contain finite non-negative stakes.")
    unresolved.setflags(write=False)
    return unresolved


@dataclass(frozen=True, slots=True)
class RiskSummary:
    """Equity-based terminal and running-peak drawdown metrics for all paths."""

    terminal_mean: float
    terminal_median: float
    terminal_standard_deviation: float
    terminal_percentile_5: float
    terminal_percentile_95: float
    probability_of_loss: float
    probability_of_ruin: float
    expected_maximum_drawdown: float
    median_maximum_drawdown: float
    path_count: int
    spin_count: int

    @property
    def number_of_paths(self) -> int:
        """Alias for report-oriented consumers."""
        return self.path_count

    @property
    def number_of_spins(self) -> int:
        """Alias for report-oriented consumers."""
        return self.spin_count


def simulate_bankroll(
    config: BankrollConfig,
    wheel: WheelSpec,
    bet: BetSpec,
    rule: SpecialRule,
    rng: np.random.Generator,
) -> BankrollSimulation:
    """Simulate seeded bankroll paths for one roulette strategy and rule.

    A single supplied generator selects one vector of pocket outcomes for each
    spin, including frozen paths, preserving deterministic common random
    numbers across comparable simulations. Existing En Prison wagers settle on
    later spins before a path may start another wager; control thresholds only
    prevent new wagers because an imprisoned wager cannot be withdrawn.
    While imprisoned, horizon equity marks liquid cash plus the stake times
    ``p_win / (p_win + p_nonzero_loss)``; settled and non-En-Prison paths have
    equity equal to liquid cash.
    """

    if not isinstance(config, BankrollConfig):
        raise TypeError("config must be a BankrollConfig.")
    if not isinstance(wheel, WheelSpec):
        raise TypeError("wheel must be a WheelSpec.")
    if not isinstance(bet, BetSpec):
        raise TypeError("bet must be a BetSpec.")
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator.")

    rule = SpecialRule(rule)
    expected_net_return(wheel, bet, rule)
    if config.custom_net_odds is not None and rule is not SpecialRule.STANDARD:
        raise ValueError("custom_net_odds is supported only with the standard rule.")

    net_odds = config.custom_net_odds if config.custom_net_odds is not None else float(bet.net_odds)
    payout_label = _payout_label(config.custom_net_odds, bet.net_odds)
    covered_indices = np.array(
        [wheel.labels.index(label) for label in bet.covered_labels], dtype=int
    )
    zero_indices = np.array(
        [index for index, label in enumerate(wheel.labels) if label in {"0", "00"}],
        dtype=int,
    )
    recovery_probability = (
        _conditional_recovery_probability(wheel, covered_indices, zero_indices)
        if rule is SpecialRule.EN_PRISON
        else 0.0
    )

    paths = np.empty((config.paths, config.spins + 1), dtype=float)
    paths[:, 0] = config.initial_bankroll
    equity_paths = paths.copy()
    frozen = np.zeros(config.paths, dtype=bool)
    imprisoned = np.zeros(config.paths, dtype=bool)
    imprisoned_stake = np.zeros(config.paths, dtype=float)
    requested_stakes = np.full(config.paths, config.base_stake, dtype=float)

    for spin in range(config.spins):
        current = paths[:, spin]
        updated = current.copy()
        outcomes = rng.choice(len(wheel.labels), size=config.paths, p=wheel.probabilities)
        outcomes_win = np.isin(outcomes, covered_indices)
        outcomes_zero = np.isin(outcomes, zero_indices)
        was_imprisoned = imprisoned.copy()

        # A prison stake was already debited on its original zero. A subsequent
        # covered pocket returns it, a non-zero loss forfeits it, and zero keeps
        # it imprisoned without replacing it with a half-loss approximation.
        settling = imprisoned & ~frozen
        settled = settling & ~outcomes_zero
        settled_wins = settled & outcomes_win
        settled_losses = settled & ~outcomes_win
        settled_stakes = imprisoned_stake.copy()
        updated[settled_wins] += settled_stakes[settled_wins]
        _advance_prison_progression(
            requested_stakes,
            settled_stakes,
            settled_wins,
            settled_losses,
            config.strategy,
            config.base_stake,
        )
        imprisoned[settled] = False
        imprisoned_stake[settled] = 0.0

        eligible = ~frozen & ~imprisoned & ~was_imprisoned
        blocked = eligible & _has_reached_threshold(current, config)
        frozen[blocked] = True
        eligible &= ~blocked

        stakes = _allowed_stakes(current, requested_stakes, eligible, config, net_odds)
        unable_to_bet = eligible & (stakes < config.min_chip)
        frozen[unable_to_bet] = True
        betting = eligible & ~unable_to_bet

        wins = betting & outcomes_win
        zeroes = betting & outcomes_zero
        losses = betting & ~outcomes_win & ~outcomes_zero

        if rule is SpecialRule.STANDARD:
            updated[wins] += net_odds * stakes[wins]
            updated[betting & ~outcomes_win] -= stakes[betting & ~outcomes_win]
        elif rule is SpecialRule.LA_PARTAGE:
            updated[wins] += net_odds * stakes[wins]
            updated[losses] -= stakes[losses]
            updated[zeroes] -= 0.5 * stakes[zeroes]
        else:
            updated[wins] += net_odds * stakes[wins]
            updated[losses] -= stakes[losses]
            updated[zeroes] -= stakes[zeroes]
            imprisoned[zeroes] = True
            imprisoned_stake[zeroes] = stakes[zeroes]

        settled_bets = betting if rule is not SpecialRule.EN_PRISON else betting & ~zeroes
        _advance_requested_stakes(
            requested_stakes, stakes, settled_bets, wins, config.strategy, config.base_stake
        )
        if rule is SpecialRule.EN_PRISON:
            requested_stakes[zeroes] = stakes[zeroes]
        paths[:, spin + 1] = updated
        equity_paths[:, spin + 1] = updated + (
            imprisoned_stake * recovery_probability
            if rule is SpecialRule.EN_PRISON
            else 0.0
        )

    return BankrollSimulation(
        config=config,
        paths=paths,
        payout_label=payout_label,
        equity_paths=equity_paths,
        unresolved_stakes=imprisoned_stake,
    )


def summarize_bankroll(simulation: BankrollSimulation) -> RiskSummary:
    """Summarize terminal outcomes and per-path maximum drawdowns."""

    if not isinstance(simulation, BankrollSimulation):
        raise TypeError("simulation must be a BankrollSimulation.")

    equity_paths = simulation.equity_paths
    terminal = equity_paths[:, -1]
    running_peaks = np.maximum.accumulate(equity_paths, axis=1)
    drawdowns = np.divide(
        running_peaks - equity_paths,
        running_peaks,
        out=np.zeros_like(equity_paths),
        where=running_peaks > 0.0,
    )
    maximum_drawdowns = drawdowns.max(axis=1)
    return RiskSummary(
        terminal_mean=float(np.mean(terminal)),
        terminal_median=float(np.median(terminal)),
        terminal_standard_deviation=float(np.std(terminal)),
        terminal_percentile_5=float(np.percentile(terminal, 5)),
        terminal_percentile_95=float(np.percentile(terminal, 95)),
        probability_of_loss=float(np.mean(terminal < simulation.config.initial_bankroll)),
        probability_of_ruin=float(np.mean(np.any(equity_paths <= 0.0, axis=1))),
        expected_maximum_drawdown=float(np.mean(maximum_drawdowns)),
        median_maximum_drawdown=float(np.median(maximum_drawdowns)),
        path_count=simulation.config.paths,
        spin_count=simulation.config.spins,
    )


def _advance_requested_stakes(
    requested_stakes: np.ndarray,
    stakes: np.ndarray,
    betting: np.ndarray,
    wins: np.ndarray,
    strategy: StrategyKind,
    base_stake: float,
) -> None:
    if strategy is StrategyKind.MARTINGALE:
        requested_stakes[betting & wins] = base_stake
        requested_stakes[betting & ~wins] = stakes[betting & ~wins] * 2.0
    elif strategy is StrategyKind.REVERSE_MARTINGALE:
        requested_stakes[betting & wins] = stakes[betting & wins] * 2.0
        requested_stakes[betting & ~wins] = base_stake


def _advance_prison_progression(
    requested_stakes: np.ndarray,
    imprisoned_stakes: np.ndarray,
    settled_wins: np.ndarray,
    settled_losses: np.ndarray,
    strategy: StrategyKind,
    base_stake: float,
) -> None:
    """Advance stake progression only after an imprisoned wager settles."""

    if strategy is StrategyKind.MARTINGALE:
        requested_stakes[settled_wins] = base_stake
        requested_stakes[settled_losses] = imprisoned_stakes[settled_losses] * 2.0
    elif strategy is StrategyKind.REVERSE_MARTINGALE:
        requested_stakes[settled_wins] = imprisoned_stakes[settled_wins] * 2.0
        requested_stakes[settled_losses] = base_stake


def _allowed_stakes(
    bankrolls: np.ndarray,
    requested_stakes: np.ndarray,
    eligible: np.ndarray,
    config: BankrollConfig,
    net_odds: float,
) -> np.ndarray:
    allowed = np.zeros_like(bankrolls)
    if config.strategy in _KELLY_STRATEGIES:
        fraction = kelly_fraction(
            config.estimated_win_probability,
            net_odds,
            _KELLY_MULTIPLIERS[config.strategy],
        )
        allowed[eligible] = bankrolls[eligible] * fraction
    else:
        allowed[eligible] = requested_stakes[eligible]
    if config.table_limit is not None:
        allowed[eligible] = np.minimum(allowed[eligible], config.table_limit)
    allowed[eligible] = np.minimum(allowed[eligible], bankrolls[eligible])
    return _round_down_to_chip(allowed, config.min_chip)


def _conditional_recovery_probability(
    wheel: WheelSpec, covered_indices: np.ndarray, zero_indices: np.ndarray
) -> float:
    """Return the En Prison stake's conditional recovery probability."""
    covered = np.zeros(len(wheel.labels), dtype=bool)
    zeroes = np.zeros(len(wheel.labels), dtype=bool)
    covered[covered_indices] = True
    zeroes[zero_indices] = True
    win_probability = float(wheel.probabilities[covered].sum())
    non_zero_loss_probability = float(wheel.probabilities[~covered & ~zeroes].sum())
    return win_probability / (win_probability + non_zero_loss_probability)


def _has_reached_threshold(bankrolls: np.ndarray, config: BankrollConfig) -> np.ndarray:
    reached = np.zeros_like(bankrolls, dtype=bool)
    if config.stop_loss is not None:
        reached |= bankrolls <= config.stop_loss
    if config.take_profit is not None:
        reached |= bankrolls >= config.take_profit
    return reached


def _round_down_to_chip(values: np.ndarray, min_chip: float) -> np.ndarray:
    rounded = np.floor(values / min_chip + 1e-12) * min_chip
    return np.minimum(rounded, values)


def _payout_label(custom_net_odds: float | None, standard_net_odds: int) -> str:
    if custom_net_odds is None:
        return f"Casino standard odds: {standard_net_odds}:1"
    return f"Custom hypothetical odds: {custom_net_odds:g}:1"


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return int(value)


def _positive_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a positive finite number.")
    numeric = float(value)
    if not np.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{name} must be a positive finite number.")
    return numeric


def _optional_positive_number(value: object, name: str) -> float | None:
    return None if value is None else _positive_number(value, name)


def _optional_nonnegative_number(value: object, name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite non-negative number.")
    numeric = float(value)
    if not np.isfinite(numeric) or numeric < 0.0:
        raise ValueError(f"{name} must be a finite non-negative number.")
    return numeric


def _unit_probability(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite probability between zero and one.")
    probability = float(value)
    if not np.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError(f"{name} must be a finite probability between zero and one.")
    return probability
