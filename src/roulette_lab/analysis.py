"""One reproducible analysis pipeline shared by reports and interfaces."""

from dataclasses import dataclass, fields
from numbers import Integral, Real
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .bankroll import (
    BankrollConfig,
    StrategyKind,
    simulate_bankroll,
    summarize_bankroll,
)
from .bets import BetKind, SpecialRule, house_edge, kelly_fraction, make_standard_bet
from .figures import publication_figures
from .io import read_spin_csv
from .statistics import (
    chi_square_fairness,
    estimate_detection_power,
    max_count_test,
    monte_carlo_global_pvalue,
)
from .wheels import WheelKind, make_fair_wheel, wheel_with_single_pocket_probability


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    """All simulation sizes, scenario settings, and random seeds in one place."""

    seed: int = 20260912
    analysis_spins: int = 20_000
    global_test_simulations: int = 10_000
    max_test_simulations: int = 10_000
    power_spins: int = 1_000
    power_experiments: int = 3_000
    bankroll_spins: int = 300
    bankroll_paths: int = 3_000
    alpha: float = 0.05
    bias_label: str = "17"
    bias_probability: float = 0.06
    initial_bankroll: float = 1_000.0
    base_stake: float = 10.0
    min_chip: float = 1.0
    table_limit: float = 100.0
    stop_loss: float = 500.0
    take_profit: float = 2_000.0

    def __post_init__(self) -> None:
        for name in (
            "seed",
            "analysis_spins",
            "global_test_simulations",
            "max_test_simulations",
            "power_spins",
            "power_experiments",
            "bankroll_spins",
            "bankroll_paths",
        ):
            value = getattr(self, name)
            minimum = 0 if name == "seed" else 1
            if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
                raise ValueError(f"{name} must be an integer at least {minimum}.")
            object.__setattr__(self, name, int(value))
        for name in (
            "initial_bankroll",
            "base_stake",
            "min_chip",
            "table_limit",
            "stop_loss",
            "take_profit",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError(f"{name} must be a finite number.")
            value = float(value)
            if not np.isfinite(value):
                raise ValueError(f"{name} must be a finite number.")
            object.__setattr__(self, name, value)
        if not 0.0 < self.alpha < 1.0:
            raise ValueError("alpha must be strictly between zero and one.")
        if not isinstance(self.bias_label, str) or not self.bias_label:
            raise ValueError("bias_label must be a non-empty pocket label.")
        if not 0.0 <= self.bias_probability <= 1.0:
            raise ValueError("bias_probability must be between zero and one.")
        if self.power_spins < 185:
            raise ValueError("power_spins must provide at least five expected spins per pocket.")
        if self.initial_bankroll <= 0 or self.base_stake <= 0 or self.min_chip <= 0:
            raise ValueError("Bankroll and stake controls must be positive.")
        if self.table_limit < self.base_stake or self.base_stake < self.min_chip:
            raise ValueError("Stake controls must satisfy min_chip <= base_stake <= table_limit.")
        if not 0 <= self.stop_loss < self.initial_bankroll < self.take_profit:
            raise ValueError("Thresholds must satisfy 0 <= stop_loss < initial < take_profit.")

    @classmethod
    def fast_test(cls) -> "AnalysisConfig":
        return cls(
            analysis_spins=800,
            global_test_simulations=400,
            max_test_simulations=400,
            power_experiments=250,
            bankroll_spins=80,
            bankroll_paths=150,
        )


@dataclass(frozen=True, slots=True, eq=False)
class AnalysisBundle:
    """Tidy, deterministic tables produced by the full analysis."""

    config: AnalysisConfig
    house_edges: pd.DataFrame
    lln_convergence: pd.DataFrame
    bias_tests: pd.DataFrame
    observed_residuals: pd.DataFrame
    detection_power: pd.DataFrame
    kelly_sensitivity: pd.DataFrame
    strategy_risk: pd.DataFrame

    @classmethod
    def table_names(cls) -> tuple[str, ...]:
        return tuple(field.name for field in fields(cls) if field.name != "config")

    def write(self, root: str | Path) -> None:
        root = Path(root)
        tables = root / "tables"
        figures = root / "figures"
        tables.mkdir(parents=True, exist_ok=True)
        figures.mkdir(parents=True, exist_ok=True)
        for name in self.table_names():
            getattr(self, name).to_csv(tables / f"{name}.csv", index=False, lineterminator="\n")
        for filename, figure in publication_figures(self).items():
            figure.savefig(
                figures / filename,
                dpi=180,
                bbox_inches="tight",
                metadata={"Software": "Roulette Analytics Lab"},
            )
            plt.close(figure)
        (root / "analysis_summary.md").write_text(
            _analysis_summary(self), encoding="utf-8"
        )


def run_full_analysis(config: AnalysisConfig) -> AnalysisBundle:
    """Run every portfolio analysis from one validated configuration."""

    if not isinstance(config, AnalysisConfig):
        raise TypeError("config must be an AnalysisConfig.")
    european = make_fair_wheel(WheelKind.EUROPEAN)
    biased = wheel_with_single_pocket_probability(
        european, config.bias_label, config.bias_probability
    )
    bias_tests, observed_residuals = _bias_tables(config, european)
    return AnalysisBundle(
        config=config,
        house_edges=_house_edge_table(),
        lln_convergence=_lln_table(config, european),
        bias_tests=bias_tests,
        observed_residuals=observed_residuals,
        detection_power=_power_table(config, european),
        kelly_sensitivity=_kelly_table(config),
        strategy_risk=_strategy_table(config, biased),
    )


def _house_edge_table() -> pd.DataFrame:
    european = make_fair_wheel(WheelKind.EUROPEAN)
    american = make_fair_wheel(WheelKind.AMERICAN)
    scenarios = (
        ("european", european, BetKind.STRAIGHT, ("17",), SpecialRule.STANDARD),
        ("american", american, BetKind.STRAIGHT, ("17",), SpecialRule.STANDARD),
        ("european_standard", european, BetKind.RED, (), SpecialRule.STANDARD),
        ("la_partage", european, BetKind.RED, (), SpecialRule.LA_PARTAGE),
        ("en_prison", european, BetKind.RED, (), SpecialRule.EN_PRISON),
    )
    rows = []
    for rule_label, wheel, kind, selection, special_rule in scenarios:
        bet = make_standard_bet(kind, selection, wheel)
        edge = house_edge(wheel, bet, special_rule)
        rows.append(
            {
                "rule": rule_label,
                "wheel": wheel.kind.value,
                "special_rule": special_rule.value,
                "bet": kind.value,
                "net_odds": bet.net_odds,
                "expected_net_return": -edge,
                "house_edge": edge,
            }
        )
    return pd.DataFrame(rows)


def _lln_table(config: AnalysisConfig, wheel) -> pd.DataFrame:
    rng = np.random.default_rng(config.seed + 1)
    target_index = wheel.labels.index(config.bias_label)
    outcomes = rng.choice(len(wheel.labels), size=config.analysis_spins, p=wheel.probabilities)
    cumulative = np.cumsum(outcomes == target_index) / np.arange(1, config.analysis_spins + 1)
    theoretical = float(wheel.probabilities[target_index])
    return pd.DataFrame(
        {
            "spin": np.arange(1, config.analysis_spins + 1),
            "label": config.bias_label,
            "empirical_probability": cumulative,
            "theoretical_probability": theoretical,
            "absolute_error": np.abs(cumulative - theoretical),
            "seed": config.seed + 1,
        }
    )


def _bias_tables(config: AnalysisConfig, wheel) -> tuple[pd.DataFrame, pd.DataFrame]:
    root = Path(__file__).resolve().parents[2]
    rows = []
    residual_rows = []
    for offset, name in enumerate(("unbiased", "biased"), start=10):
        dataset = read_spin_csv(root / "data" / f"example_{name}_spins.csv", wheel)
        counts = np.array([dataset.spins.count(label) for label in wheel.labels], dtype=int)
        fairness = chi_square_fairness(counts, wheel)
        global_mc = monte_carlo_global_pvalue(
            counts,
            wheel,
            config.global_test_simulations,
            np.random.default_rng(config.seed + offset),
        )
        maximum = max_count_test(
            counts,
            wheel,
            config.max_test_simulations,
            np.random.default_rng(config.seed + offset + 20),
        )
        hottest_index = int(np.argmax(counts))
        rows.append(
            {
                "dataset": name,
                "spins": int(counts.sum()),
                "hottest_label": wheel.labels[hottest_index],
                "observed_max": maximum.observed_max,
                "chi_square_statistic": fairness.statistic,
                "asymptotic_p_value": fairness.p_value,
                "monte_carlo_global_p_value": global_mc,
                "naive_p_value": maximum.naive_p_value,
                "bonferroni_p_value": maximum.bonferroni_p_value,
                "familywise_p_value": maximum.familywise_p_value,
                "alpha": config.alpha,
            }
        )
        residual_rows.extend(
            {
                "dataset": name,
                "label": label,
                "observed_count": int(count),
                "expected_count": expected,
                "pearson_residual": residual,
            }
            for label, count, expected, residual in zip(
                wheel.labels,
                counts,
                fairness.expected_counts,
                fairness.pearson_residuals,
                strict=True,
            )
        )
    return pd.DataFrame(rows), pd.DataFrame(residual_rows)


def _power_table(config: AnalysisConfig, null_wheel) -> pd.DataFrame:
    fair_probability = 1 / len(null_wheel.labels)
    upper = max(config.bias_probability, 0.08)
    probabilities = np.unique(
        np.concatenate(([fair_probability], np.linspace(0.035, upper, 7)))
    )
    rows = []
    for index, probability in enumerate(probabilities):
        alternative = wheel_with_single_pocket_probability(
            null_wheel, config.bias_label, float(probability)
        )
        estimate = estimate_detection_power(
            null_wheel,
            alternative,
            config.power_spins,
            config.alpha,
            config.power_experiments,
            np.random.default_rng(config.seed + 100 + index),
        )
        rows.append(
            {
                "label": config.bias_label,
                "pocket_probability": float(probability),
                "estimated_power": estimate.estimated_power,
                "monte_carlo_standard_error": estimate.monte_carlo_standard_error,
                "spins": estimate.spins,
                "experiments": estimate.experiments,
                "alpha": estimate.alpha,
                "seed": config.seed + 100 + index,
            }
        )
    return pd.DataFrame(rows)


def _kelly_table(config: AnalysisConfig) -> pd.DataFrame:
    probabilities = np.unique(
        np.concatenate((np.linspace(0.02, 0.08, 25), [1 / 37, 1 / 36, config.bias_probability]))
    )
    return pd.DataFrame(
        {
            "pocket_probability": probabilities,
            "break_even_probability": 1 / 36,
            "full_kelly": [kelly_fraction(value, 35, 1.0) for value in probabilities],
            "half_kelly": [kelly_fraction(value, 35, 0.5) for value in probabilities],
            "quarter_kelly": [kelly_fraction(value, 35, 0.25) for value in probabilities],
        }
    )


def _strategy_table(config: AnalysisConfig, wheel) -> pd.DataFrame:
    bet = make_standard_bet(BetKind.STRAIGHT, (config.bias_label,), wheel)
    strategies = (
        StrategyKind.FLAT,
        StrategyKind.MARTINGALE,
        StrategyKind.REVERSE_MARTINGALE,
        StrategyKind.FULL_KELLY,
        StrategyKind.HALF_KELLY,
        StrategyKind.QUARTER_KELLY,
    )
    rows = []
    for index, strategy in enumerate(strategies):
        bankroll_config = BankrollConfig(
            initial_bankroll=config.initial_bankroll,
            base_stake=config.base_stake,
            spins=config.bankroll_spins,
            paths=config.bankroll_paths,
            strategy=strategy,
            estimated_win_probability=(
                config.bias_probability if "kelly" in strategy.value else None
            ),
            min_chip=config.min_chip,
            table_limit=config.table_limit,
            stop_loss=config.stop_loss,
            take_profit=config.take_profit,
        )
        simulation = simulate_bankroll(
            bankroll_config,
            wheel,
            bet,
            SpecialRule.STANDARD,
            np.random.default_rng(config.seed + 200 + index),
        )
        summary = summarize_bankroll(simulation)
        rows.append(
            {
                "strategy": strategy.value,
                "wheel_scenario": f"{config.bias_label} at {config.bias_probability:.3f}",
                "payout_label": simulation.payout_label,
                "terminal_mean": summary.terminal_mean,
                "terminal_median": summary.terminal_median,
                "terminal_standard_deviation": summary.terminal_standard_deviation,
                "terminal_percentile_5": summary.terminal_percentile_5,
                "terminal_percentile_95": summary.terminal_percentile_95,
                "probability_of_loss": summary.probability_of_loss,
                "probability_of_ruin": summary.probability_of_ruin,
                "expected_maximum_drawdown": summary.expected_maximum_drawdown,
                "median_maximum_drawdown": summary.median_maximum_drawdown,
                "paths": summary.path_count,
                "spins": summary.spin_count,
                "seed": config.seed + 200 + index,
            }
        )
    return pd.DataFrame(rows)


def _analysis_summary(bundle: AnalysisBundle) -> str:
    biased = bundle.bias_tests.loc[bundle.bias_tests["dataset"] == "biased"].iloc[0]
    best_power = bundle.detection_power.iloc[-1]
    return (
        "# Reproducible analysis summary\n\n"
        "## Selection-aware bias evidence\n\n"
        f"The biased example's hottest pocket was `{biased.hottest_label}`. Its naive "
        f"p-value was {biased.naive_p_value:.4f}, while the selection-aware family-wise "
        f"p-value was {biased.familywise_p_value:.4f}. The latter is the relevant result "
        "after choosing the hottest pocket from the same sample.\n\n"
        "## Detection power\n\n"
        f"At pocket probability {best_power.pocket_probability:.3f}, the global test's "
        f"estimated power was {best_power.estimated_power:.3f} "
        f"(Monte Carlo SE {best_power.monte_carlo_standard_error:.3f}).\n\n"
        "## Bankroll and Kelly interpretation\n\n"
        "Kelly sizing is conditional on a correct probability and payout model. It is an "
        "expected log-growth rule, not guaranteed profit. Strategy tables report simulated "
        "terminal dispersion, loss risk, ruin risk, and maximum drawdown under a declared "
        "biased-wheel scenario.\n"
    )
