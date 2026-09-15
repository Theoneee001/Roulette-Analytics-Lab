"""Immutable, reproducible live roulette experiment state."""

from dataclasses import dataclass, field, replace
from numbers import Integral, Real

import numpy as np
from numpy.typing import NDArray

from .bets import BetSpec, SpecialRule, expected_net_return
from .wheels import WheelKind, WheelSpec


@dataclass(frozen=True, slots=True)
class _WheelSignature:
    kind: WheelKind
    labels: tuple[str, ...]
    colours: tuple[str, ...]
    probabilities: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class _PendingWager:
    rule: SpecialRule
    bet: BetSpec
    wheel: _WheelSignature


@dataclass(frozen=True, slots=True)
class ExperimentState:
    """A replayable roulette experiment with no mutable random generator."""

    seed: int
    initial_bankroll: float
    history: tuple[str, ...] = ()
    bankroll: float = 0.0
    imprisoned_stake: float = 0.0
    _pending_wager: _PendingWager | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        seed = _nonnegative_integer(self.seed, "seed")
        initial_bankroll = _positive_finite(self.initial_bankroll, "initial_bankroll")
        history = _history(self.history)
        bankroll = _nonnegative_finite(self.bankroll, "bankroll")
        imprisoned_stake = _nonnegative_finite(self.imprisoned_stake, "imprisoned_stake")
        pending_wager = self._pending_wager
        if pending_wager is not None and not isinstance(pending_wager, _PendingWager):
            raise TypeError("_pending_wager must be pending-wager configuration or None.")
        if (imprisoned_stake > 0.0) != (pending_wager is not None):
            raise ValueError(
                "An imprisoned_stake requires its originating pending-wager configuration."
            )
        object.__setattr__(self, "seed", seed)
        object.__setattr__(self, "initial_bankroll", initial_bankroll)
        object.__setattr__(self, "history", history)
        object.__setattr__(self, "bankroll", bankroll)
        object.__setattr__(self, "imprisoned_stake", imprisoned_stake)

    def counts(self, wheel: WheelSpec) -> NDArray[np.int64]:
        """Return pocket counts in the supplied wheel's label order."""
        _wheel(wheel)
        return np.array([self.history.count(label) for label in wheel.labels], dtype=np.int64)

    def indicators(self, label: str) -> NDArray[np.int64]:
        """Return one for each recorded occurrence of ``label`` and zero otherwise."""
        if not isinstance(label, str) or not label:
            raise ValueError("label must be a non-empty string.")
        return np.fromiter((value == label for value in self.history), dtype=np.int64)


def new_experiment(seed: int, initial_bankroll: float) -> ExperimentState:
    """Create an empty experiment from a reproducible seed and bankroll."""
    return ExperimentState(
        seed=_nonnegative_integer(seed, "seed"),
        initial_bankroll=_positive_finite(initial_bankroll, "initial_bankroll"),
        bankroll=float(initial_bankroll),
    )


def advance_experiment(
    state: ExperimentState,
    wheel: WheelSpec,
    bet: BetSpec,
    rule: SpecialRule,
    stake: float,
    count: int,
) -> ExperimentState:
    """Draw and settle reproducible roulette spins without mutating ``state``."""
    if not isinstance(state, ExperimentState):
        raise TypeError("state must be an ExperimentState.")
    _wheel(wheel)
    if not isinstance(bet, BetSpec):
        raise TypeError("bet must be a BetSpec.")
    rule = SpecialRule(rule)
    stake = _positive_finite(stake, "stake")
    count = _positive_integer(count, "count")
    _validate_pending_wager(state, wheel, bet, rule)
    expected_net_return(wheel, bet, rule)
    _validate_history_membership(state.history, wheel)

    rng = np.random.default_rng(state.seed)
    draws = rng.choice(
        np.asarray(wheel.labels, dtype=object),
        size=len(state.history) + count,
        p=wheel.probabilities,
    )
    appended = tuple(str(value) for value in draws[-count:])
    bankroll, imprisoned_stake, pending_wager = _settle(
        state.bankroll,
        state.imprisoned_stake,
        state._pending_wager,
        appended,
        wheel,
        bet,
        rule,
        stake,
    )
    return replace(
        state,
        history=state.history + appended,
        bankroll=bankroll,
        imprisoned_stake=imprisoned_stake,
        _pending_wager=pending_wager,
    )


def reset_experiment(state: ExperimentState) -> ExperimentState:
    """Restore an experiment to its seeded initial bankroll state."""
    if not isinstance(state, ExperimentState):
        raise TypeError("state must be an ExperimentState.")
    return new_experiment(state.seed, state.initial_bankroll)


def _settle(
    bankroll: float,
    imprisoned_stake: float,
    pending_wager: _PendingWager | None,
    results: tuple[str, ...],
    wheel: WheelSpec,
    bet: BetSpec,
    rule: SpecialRule,
    stake: float,
) -> tuple[float, float, _PendingWager | None]:
    covered_labels = frozenset(bet.covered_labels)
    for result in results:
        is_zero = result in {"0", "00"}
        is_win = result in covered_labels
        if rule is SpecialRule.EN_PRISON and imprisoned_stake > 0.0:
            if not is_zero:
                if is_win:
                    bankroll += imprisoned_stake
                imprisoned_stake = 0.0
                pending_wager = None
            continue

        wager = min(stake, bankroll)
        if wager == 0.0:
            continue
        if is_win:
            bankroll += wager * bet.net_odds
        elif rule is SpecialRule.LA_PARTAGE and is_zero:
            bankroll -= wager * 0.5
        else:
            bankroll -= wager
            if rule is SpecialRule.EN_PRISON and is_zero:
                imprisoned_stake = wager
                pending_wager = _pending_wager_configuration(wheel, bet, rule)
    return float(bankroll), float(imprisoned_stake), pending_wager


def _wheel(wheel: WheelSpec) -> WheelSpec:
    if not isinstance(wheel, WheelSpec):
        raise TypeError("wheel must be a WheelSpec.")
    return wheel


def _validate_history_membership(history: tuple[str, ...], wheel: WheelSpec) -> None:
    if set(history) - set(wheel.labels):
        raise ValueError("history labels must all be present on wheel.")


def _validate_pending_wager(
    state: ExperimentState,
    wheel: WheelSpec,
    bet: BetSpec,
    rule: SpecialRule,
) -> None:
    if state.imprisoned_stake == 0.0:
        return
    if state._pending_wager != _pending_wager_configuration(wheel, bet, rule):
        raise ValueError(
            "Cannot change rule, bet, or wheel while an unresolved En Prison wager exists."
        )


def _pending_wager_configuration(
    wheel: WheelSpec, bet: BetSpec, rule: SpecialRule
) -> _PendingWager:
    return _PendingWager(
        rule=rule,
        bet=bet,
        wheel=_WheelSignature(
            kind=wheel.kind,
            labels=wheel.labels,
            colours=wheel.colours,
            probabilities=tuple(float(value) for value in wheel.probabilities),
        ),
    )


def _history(history: object) -> tuple[str, ...]:
    if not isinstance(history, tuple) or any(
        not isinstance(label, str) or not label for label in history
    ):
        raise ValueError("history must be a tuple of non-empty strings.")
    return history


def _positive_integer(value: object, name: str) -> int:
    value = _nonnegative_integer(value, name)
    if value == 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def _nonnegative_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < 0:
        raise ValueError(f"{name} must be a non-negative integer.")
    return int(value)


def _positive_finite(value: object, name: str) -> float:
    value = _finite_number(value, name)
    if value <= 0.0:
        raise ValueError(f"{name} must be a positive finite number.")
    return value


def _nonnegative_finite(value: object, name: str) -> float:
    value = _finite_number(value, name)
    if value < 0.0:
        raise ValueError(f"{name} must be a non-negative finite number.")
    return value


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number.")
    value = float(value)
    if not np.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    return value
