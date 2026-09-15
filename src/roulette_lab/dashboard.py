"""Testable view models for the Streamlit analytical workspace."""

from dataclasses import dataclass, fields, replace
from numbers import Integral, Real
from typing import Mapping

import numpy as np
import pandas as pd

from .bankroll import BankrollConfig, RiskSummary, StrategyKind, simulate_bankroll, summarize_bankroll
from .bets import BetKind, SpecialRule, house_edge, kelly_fraction, make_standard_bet
from .decision import PosteriorEdgeSummary, posterior_edge_summary
from .experiment import ExperimentState
from .io import SpinDataset
from .risk import build_risk_frontier
from .sequential import CUSUMResult, SequentialEvidence, cusum_change_detection, likelihood_ratio_path
from .statistics import chi_square_fairness, max_count_test, monte_carlo_global_pvalue
from .wheels import WheelKind, make_fair_wheel, wheel_with_single_pocket_probability


@dataclass(frozen=True, slots=True)
class DashboardInputs:
    wheel_kind: str = "european"
    rule: str = "standard"
    bet_kind: str = "straight"
    selection: tuple[str, ...] = ("17",)
    initial_bankroll: float = 1_000.0
    base_stake: float = 10.0
    stop_loss: float = 500.0
    take_profit: float = 2_000.0
    paths: int = 500
    spins: int = 200
    strategy: str = "flat"
    estimated_win_probability: float | None = None
    min_chip: float = 1.0
    table_limit: float = 100.0
    bias_label: str = "17"
    bias_probability: float = 1 / 37
    alpha: float = 0.05
    simulations: int = 2_000
    seed: int = 20260912
    odds_mode: str = "Casino standard"
    custom_net_odds: float | None = None
    target_probability: float = 0.60
    cusum_threshold: float = 3.0
    posterior_prior_strength: float = 37.0
    credible_level: float = 0.95
    conservative_quantile: float = 0.10
    future_spins: int = 100
    cvar_level: float = 0.05
    live_stake: float = 10.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "wheel_kind", WheelKind(self.wheel_kind).value)
        object.__setattr__(self, "rule", SpecialRule(self.rule).value)
        object.__setattr__(self, "bet_kind", BetKind(self.bet_kind).value)
        object.__setattr__(self, "strategy", StrategyKind(self.strategy).value)
        object.__setattr__(self, "selection", tuple(self.selection))
        if self.odds_mode not in {"Casino standard", "Custom hypothetical"}:
            raise ValueError("odds_mode must be Casino standard or Custom hypothetical.")
        for name in ("initial_bankroll", "base_stake", "min_chip", "table_limit"):
            _require_positive(getattr(self, name), name)
        if not _is_number(self.stop_loss) or not 0 <= self.stop_loss < self.initial_bankroll:
            raise ValueError("stop_loss must be below the initial bankroll and non-negative.")
        if not _is_number(self.take_profit) or self.take_profit <= self.initial_bankroll:
            raise ValueError("take_profit must be above the initial bankroll.")
        for name in ("paths", "spins", "simulations"):
            _require_positive_integer(getattr(self, name), name)
        if isinstance(self.seed, bool) or not isinstance(self.seed, Integral) or self.seed < 0:
            raise ValueError("seed must be a non-negative integer.")
        if not _is_number(self.alpha) or not 0 < self.alpha < 1:
            raise ValueError("alpha must be strictly between zero and one.")
        if not isinstance(self.bias_label, str) or not self.bias_label:
            raise ValueError("bias_label must be a pocket label.")
        if not _is_number(self.bias_probability) or not 0 <= self.bias_probability <= 1:
            raise ValueError("bias_probability must be between zero and one.")
        if self.estimated_win_probability is not None and (
            not _is_number(self.estimated_win_probability)
            or not 0 <= self.estimated_win_probability <= 1
        ):
            raise ValueError("estimated_win_probability must be between zero and one.")
        if self.odds_mode == "Custom hypothetical":
            _require_positive(self.custom_net_odds, "custom_net_odds")
        elif self.custom_net_odds is not None:
            raise ValueError("custom_net_odds requires Custom hypothetical mode.")
        for name in ("target_probability", "credible_level", "conservative_quantile", "cvar_level"):
            if not _is_number(getattr(self, name)) or not 0 < getattr(self, name) < 1:
                raise ValueError(f"{name} must be strictly between zero and one.")
        for name in ("cusum_threshold", "posterior_prior_strength", "live_stake"):
            _require_positive(getattr(self, name), name)
        _require_positive_integer(self.future_spins, "future_spins")

    @classmethod
    def fast_test(cls) -> "DashboardInputs":
        return cls(paths=40, spins=30, simulations=300)


@dataclass(frozen=True, slots=True)
class WheelView:
    standard_house_edge: float
    standard_expected_net_return: float
    standard_payout_label: str
    simulation_payout_label: str
    scenario_notice: str
    probabilities: pd.DataFrame
    zero_pockets: tuple[str, ...]
    table_geometry: pd.DataFrame


@dataclass(frozen=True, slots=True)
class FairnessView:
    counts: pd.DataFrame
    chi_square_statistic: float
    asymptotic_p_value: float
    monte_carlo_global_p_value: float
    naive_p_value: float
    bonferroni_p_value: float
    familywise_p_value: float
    hottest_label: str
    selection_warning: str
    sample_warning: str | None


@dataclass(frozen=True, slots=True)
class BankrollView:
    path_data: np.ndarray
    equity_data: np.ndarray
    risk: RiskSummary
    payout_label: str
    scenario_notice: str
    no_edge_message: str | None
    summary_table: pd.DataFrame


@dataclass(frozen=True, slots=True)
class EvidenceView:
    """Sequential evidence diagnostics derived from the current experiment."""

    evidence: SequentialEvidence | None
    cusum: CUSUMResult | None
    p0: float
    p1: float
    no_alarm_message: str | None


@dataclass(frozen=True, slots=True)
class LiveExperimentView:
    """A single history-backed view for the live experiment tab."""

    sample_size: int
    hits: int
    bankroll: float
    result: str | None
    running_frequency: np.ndarray
    posterior_band: tuple[np.ndarray, np.ndarray]
    e_values: np.ndarray
    log10_evidence: np.ndarray
    log10_threshold: float
    cusum_scores: np.ndarray
    posterior: PosteriorEdgeSummary
    evidence: EvidenceView
    fairness: FairnessView | None
    empty_message: str | None


@dataclass(frozen=True, slots=True)
class DecisionRiskView:
    """Posterior decision and forward bankroll risk results."""

    posterior: PosteriorEdgeSummary
    frontier: pd.DataFrame
    bankroll: BankrollView
    no_edge_message: str | None
    decision_probability: float
    cvar_level: float


def validate_dashboard_inputs(values: Mapping[str, object]) -> DashboardInputs:
    """Merge widget values with defaults and return one validated input model."""

    if not isinstance(values, Mapping):
        raise TypeError("values must be a mapping.")
    allowed = {field.name for field in fields(DashboardInputs)}
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"Unknown dashboard inputs: {sorted(unknown)}")
    defaults = DashboardInputs()
    merged = {name: getattr(defaults, name) for name in allowed}
    merged.update(values)
    return DashboardInputs(**merged)


def build_wheel_view(inputs: DashboardInputs) -> WheelView:
    wheel, bet, rule = _scenario(inputs)
    edge = house_edge(wheel, bet, rule)
    custom = inputs.custom_net_odds if inputs.odds_mode == "Custom hypothetical" else None
    simulation_label = (
        f"Custom hypothetical odds: {custom:g}:1"
        if custom is not None
        else f"Casino standard odds: {bet.net_odds}:1"
    )
    notice = (
        "Custom hypothetical odds change simulation payouts only. Exact casino economics stay at standard odds."
        if custom is not None
        else "Exact casino economics and simulations use the standard payout."
    )
    return WheelView(
        standard_house_edge=edge,
        standard_expected_net_return=-edge,
        standard_payout_label=f"Casino standard odds: {bet.net_odds}:1",
        simulation_payout_label=simulation_label,
        scenario_notice=notice,
        probabilities=pd.DataFrame(
            {
                "label": wheel.labels,
                "colour": wheel.colours,
                "probability": wheel.probabilities,
            }
        ),
        zero_pockets=tuple(label for label in wheel.labels if label in {"0", "00"}),
        table_geometry=pd.DataFrame(
            {
                "low": [str(value) for value in range(1, 35, 3)],
                "middle": [str(value) for value in range(2, 36, 3)],
                "high": [str(value) for value in range(3, 37, 3)],
            }
        ),
    )


def build_fairness_view(dataset: SpinDataset, inputs: DashboardInputs) -> FairnessView:
    if not isinstance(dataset, SpinDataset):
        raise TypeError("dataset must be a SpinDataset.")
    wheel_kind = WheelKind(inputs.wheel_kind)
    if dataset.wheel_kind is not wheel_kind:
        raise ValueError("Dataset wheel kind must match the selected dashboard wheel.")
    wheel = make_fair_wheel(wheel_kind)
    counts = np.array([dataset.spins.count(label) for label in wheel.labels], dtype=int)
    fairness = chi_square_fairness(counts, wheel)
    global_p = monte_carlo_global_pvalue(
        counts, wheel, inputs.simulations, np.random.default_rng(inputs.seed + 1)
    )
    maximum = max_count_test(
        counts, wheel, inputs.simulations, np.random.default_rng(inputs.seed + 2)
    )
    hottest_index = int(np.argmax(counts))
    return FairnessView(
        counts=pd.DataFrame(
            {
                "label": wheel.labels,
                "observed": counts,
                "expected": fairness.expected_counts,
                "residual": fairness.pearson_residuals,
            }
        ),
        chi_square_statistic=fairness.statistic,
        asymptotic_p_value=fairness.p_value,
        monte_carlo_global_p_value=global_p,
        naive_p_value=maximum.naive_p_value,
        bonferroni_p_value=maximum.bonferroni_p_value,
        familywise_p_value=maximum.familywise_p_value,
        hottest_label=wheel.labels[hottest_index],
        selection_warning=(
            "The hottest pocket was selected after observing this sample. Use the "
            "family-wise p-value for that data-dependent claim, not the naive p-value."
        ),
        sample_warning=fairness.warning,
    )


def build_bankroll_view(inputs: DashboardInputs) -> BankrollView:
    wheel, bet, rule = _scenario(inputs)
    custom = inputs.custom_net_odds if inputs.odds_mode == "Custom hypothetical" else None
    strategy = StrategyKind(inputs.strategy)
    estimated = inputs.estimated_win_probability
    if "kelly" in strategy.value and estimated is None:
        estimated = sum(
            probability
            for label, probability in zip(wheel.labels, wheel.probabilities, strict=True)
            if label in bet.covered_labels
        )
    config = BankrollConfig(
        initial_bankroll=inputs.initial_bankroll,
        base_stake=inputs.base_stake,
        spins=inputs.spins,
        paths=inputs.paths,
        strategy=strategy,
        estimated_win_probability=estimated,
        min_chip=inputs.min_chip,
        table_limit=inputs.table_limit,
        stop_loss=inputs.stop_loss,
        take_profit=inputs.take_profit,
        custom_net_odds=custom,
    )
    simulation = simulate_bankroll(
        config, wheel, bet, rule, np.random.default_rng(inputs.seed)
    )
    risk = summarize_bankroll(simulation, inputs.cvar_level)
    no_edge = None
    if "kelly" in strategy.value and kelly_fraction(estimated, custom or bet.net_odds) == 0:
        no_edge = "The estimated edge does not clear break-even, so Kelly allocates no stake."
    notice = (
        "Hypothetical payout scenario; it does not change the standard casino house-edge result."
        if custom is not None
        else "Casino standard payout scenario."
    )
    summary = pd.DataFrame(
        [
            {
                "terminal_mean": risk.terminal_mean,
                "terminal_median": risk.terminal_median,
                "terminal_standard_deviation": risk.terminal_standard_deviation,
                "percentile_5": risk.terminal_percentile_5,
                "percentile_95": risk.terminal_percentile_95,
                "probability_of_loss": risk.probability_of_loss,
                "probability_of_ruin": risk.probability_of_ruin,
                "expected_maximum_drawdown": risk.expected_maximum_drawdown,
                "paths": risk.path_count,
                "spins": risk.spin_count,
                "payout_scenario": simulation.payout_label,
            }
        ]
    )
    return BankrollView(
        path_data=simulation.paths,
        equity_data=simulation.equity_paths,
        risk=risk,
        payout_label=simulation.payout_label,
        scenario_notice=notice,
        no_edge_message=no_edge,
        summary_table=summary,
    )


def build_live_experiment_view(state: ExperimentState, inputs: DashboardInputs) -> LiveExperimentView:
    """Compose live frequencies, posterior uncertainty, and sequential evidence."""

    if not isinstance(state, ExperimentState):
        raise TypeError("state must be an ExperimentState.")
    wheel, bet, _ = _scenario(inputs)
    if set(state.history) - set(wheel.labels):
        raise ValueError("experiment history must match the selected wheel.")
    p0 = float(sum(probability for label, probability in zip(wheel.labels, wheel.probabilities, strict=True) if label in bet.covered_labels))
    p1 = float(inputs.target_probability)
    if p1 <= p0:
        raise ValueError("target_probability must exceed the selected bet probability.")
    observations = np.asarray([label in bet.covered_labels for label in state.history], dtype=np.int64)
    hits = int(observations.sum())
    prior_alpha = p0 * inputs.posterior_prior_strength
    prior_beta = (1.0 - p0) * inputs.posterior_prior_strength
    posterior = posterior_edge_summary(
        hits, len(observations), prior_alpha, prior_beta, bet.net_odds,
        inputs.credible_level, inputs.conservative_quantile, inputs.future_spins,
    )
    if observations.size == 0:
        empty = "No spins recorded. Run a single spin or a batch to initialise the evidence paths."
        return LiveExperimentView(
            sample_size=0, hits=0, bankroll=state.bankroll, result=None,
            running_frequency=np.array([], dtype=float),
            posterior_band=(np.array([], dtype=float), np.array([], dtype=float)),
            e_values=np.array([], dtype=float),
            log10_evidence=np.array([], dtype=float),
            log10_threshold=float(-np.log(inputs.alpha) / np.log(10.0)),
            cusum_scores=np.array([], dtype=float),
            posterior=posterior,
            evidence=EvidenceView(None, None, p0, p1, "CUSUM is waiting for observations."),
            fairness=None,
            empty_message=empty,
        )
    running_frequency = np.cumsum(observations, dtype=float) / np.arange(1, observations.size + 1)
    lower, upper = _posterior_bands(observations, prior_alpha, prior_beta, inputs.credible_level)
    evidence = likelihood_ratio_path(observations, p0, p1, inputs.alpha)
    cusum = cusum_change_detection(observations, p0, p1, inputs.cusum_threshold)
    evidence_view = EvidenceView(
        evidence=evidence,
        cusum=cusum,
        p0=p0,
        p1=p1,
        no_alarm_message=None if cusum.first_alarm is not None else "No CUSUM alarm has crossed the declared threshold.",
    )
    fair_wheel = make_fair_wheel(WheelKind(inputs.wheel_kind))
    fairness = build_fairness_view(
        SpinDataset(
            spin_indices=tuple(range(1, len(state.history) + 1)),
            spins=state.history,
            wheel_kind=fair_wheel.kind,
            wheel_labels=fair_wheel.labels,
            wheel_probabilities=tuple(float(value) for value in fair_wheel.probabilities),
        ),
        inputs,
    )
    return LiveExperimentView(
        sample_size=int(observations.size), hits=hits, bankroll=state.bankroll,
        result=state.history[-1], running_frequency=running_frequency,
        posterior_band=(lower, upper), e_values=evidence.e_values,
        log10_evidence=evidence.log_likelihood_ratio / np.log(10.0),
        log10_threshold=float(-np.log(inputs.alpha) / np.log(10.0)),
        cusum_scores=cusum.scores, posterior=posterior, evidence=evidence_view,
        fairness=fairness,
        empty_message=None,
    )


def build_decision_risk_view(state: ExperimentState, inputs: DashboardInputs) -> DecisionRiskView:
    """Return the posterior decision and common-random-number risk frontier."""

    live = build_live_experiment_view(state, inputs)
    wheel, bet, rule = _scenario(inputs)
    config = BankrollConfig(
        initial_bankroll=inputs.initial_bankroll, base_stake=inputs.base_stake,
        spins=inputs.spins, paths=inputs.paths, strategy=StrategyKind.FLAT,
        estimated_win_probability=live.posterior.posterior_mean, min_chip=inputs.min_chip,
        table_limit=inputs.table_limit, stop_loss=inputs.stop_loss, take_profit=inputs.take_profit,
        custom_net_odds=inputs.custom_net_odds if inputs.odds_mode == "Custom hypothetical" else None,
    )
    frontier = build_risk_frontier(
        config,
        wheel,
        bet,
        rule,
        [0.25, 0.5, 1.0],
        inputs.seed,
        tail_probability=inputs.cvar_level,
    )
    no_edge = (
        "The posterior does not put more than half its mass above break-even. Kelly outputs are shown as zero-stake evidence."
        if live.posterior.probability_positive_edge <= 0.5 else None
    )
    decision_probability = live.posterior.posterior_mean
    decision_inputs = replace(
        inputs,
        strategy=StrategyKind.FULL_KELLY.value,
        estimated_win_probability=decision_probability,
    )
    return DecisionRiskView(
        live.posterior,
        frontier,
        build_bankroll_view(decision_inputs),
        no_edge,
        decision_probability,
        inputs.cvar_level,
    )


def _scenario(inputs: DashboardInputs):
    if not isinstance(inputs, DashboardInputs):
        raise TypeError("inputs must be DashboardInputs.")
    wheel = make_fair_wheel(WheelKind(inputs.wheel_kind))
    if inputs.bias_label not in wheel.labels:
        raise ValueError("bias_label is not present on the selected wheel.")
    wheel = wheel_with_single_pocket_probability(
        wheel, inputs.bias_label, inputs.bias_probability
    )
    bet = make_standard_bet(BetKind(inputs.bet_kind), inputs.selection, wheel)
    rule = SpecialRule(inputs.rule)
    house_edge(wheel, bet, rule)
    return wheel, bet, rule


def _posterior_bands(
    observations: np.ndarray, prior_alpha: float, prior_beta: float, level: float
) -> tuple[np.ndarray, np.ndarray]:
    """Return an expanding Beta posterior interval at every observed spin."""

    import scipy.stats

    cumulative_hits = np.cumsum(observations, dtype=float)
    trials = np.arange(1, observations.size + 1, dtype=float)
    tail = (1.0 - level) / 2.0
    lower = scipy.stats.beta.ppf(tail, prior_alpha + cumulative_hits, prior_beta + trials - cumulative_hits)
    upper = scipy.stats.beta.ppf(1.0 - tail, prior_alpha + cumulative_hits, prior_beta + trials - cumulative_hits)
    return np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)


def _is_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, Real)
        and np.isfinite(float(value))
    )


def _require_positive(value: object, name: str) -> float:
    if not _is_number(value) or float(value) <= 0:
        raise ValueError(f"{name} must be a positive finite number.")
    return float(value)


def _require_positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return int(value)
