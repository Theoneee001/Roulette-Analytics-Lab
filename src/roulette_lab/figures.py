"""Publication figures for the roulette analysis bundle."""

from collections.abc import Mapping
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats
from matplotlib.figure import Figure

from .wheels import WheelKind, make_fair_wheel

if TYPE_CHECKING:
    from .analysis import AnalysisBundle


_INK = "#17211d"
_GREEN = "#12634f"
_RED = "#bd3c3c"
_GOLD = "#b4862d"
_BLUE = "#356f9f"
_PAPER = "#f7f5ef"

EUROPEAN_WHEEL_ORDER = (
    "0", "32", "15", "19", "4", "21", "2", "25", "17", "34", "6", "27", "13",
    "36", "11", "30", "8", "23", "10", "5", "24", "16", "33", "1", "20", "14",
    "31", "9", "22", "18", "29", "7", "28", "12", "35", "3", "26",
)


def _axes(title: str, xlabel: str = "", ylabel: str = ""):
    figure, axis = plt.subplots(figsize=(10, 6), facecolor=_PAPER)
    axis.set_facecolor(_PAPER)
    axis.set_title(title, loc="left", fontsize=15, color=_INK, pad=14)
    axis.set_xlabel(xlabel, color=_INK)
    axis.set_ylabel(ylabel, color=_INK)
    axis.grid(axis="y", color="#d8d4c9", linewidth=0.7, alpha=0.8)
    axis.spines[["top", "right"]].set_visible(False)
    return figure, axis


def wheel_layout_figure() -> Figure:
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    colour_by_label = dict(zip(wheel.labels, wheel.colours, strict=True))
    angles = np.linspace(0, 2 * np.pi, len(EUROPEAN_WHEEL_ORDER), endpoint=False)
    colours = [
        _GREEN if colour == "green" else _RED if colour == "red" else _INK
        for colour in (colour_by_label[label] for label in EUROPEAN_WHEEL_ORDER)
    ]
    figure = plt.figure(figsize=(9, 9), facecolor=_PAPER)
    axis = figure.add_subplot(projection="polar")
    axis.set_facecolor(_PAPER)
    axis.bar(
        angles,
        np.ones(len(angles)),
        width=2 * np.pi / len(angles),
        bottom=0.35,
        color=colours,
        edgecolor=_PAPER,
        linewidth=1,
    )
    for angle, label in zip(angles, EUROPEAN_WHEEL_ORDER, strict=True):
        axis.text(angle, 0.88, label, color="white", ha="center", va="center", fontsize=7)
    axis.set_ylim(0, 1.35)
    axis.set_axis_off()
    axis.set_title("European roulette pockets", fontsize=15, color=_INK, pad=18)
    return figure


def house_edge_figure(table: pd.DataFrame) -> Figure:
    _require_columns(table, "rule", "house_edge")
    figure, axis = _axes("House edge by wheel and rule", ylabel="House edge (%)")
    values = 100 * table["house_edge"].to_numpy()
    bars = axis.bar(table["rule"], values, color=[_GREEN, _RED, _INK, _GOLD, _BLUE])
    axis.bar_label(bars, fmt="%.2f%%", padding=3, fontsize=9)
    axis.tick_params(axis="x", rotation=18)
    return figure


def lln_convergence_figure(table: pd.DataFrame) -> Figure:
    _require_columns(table, "spin", "empirical_probability", "theoretical_probability")
    figure, axis = _axes(
        "Law of large numbers: one pocket", "Spins", "Cumulative probability"
    )
    axis.plot(table["spin"], table["empirical_probability"], color=_BLUE, label="Observed")
    axis.plot(
        table["spin"],
        table["theoretical_probability"],
        color=_RED,
        linestyle="--",
        label="Fair-wheel probability",
    )
    axis.legend(frameon=False)
    return figure


def residual_figure(table: pd.DataFrame) -> Figure:
    _require_columns(table, "dataset", "label", "pearson_residual")
    subset = table.loc[table["dataset"] == "biased"]
    figure, axis = _axes(
        "Observed versus expected: biased example", "Pocket", "Pearson residual"
    )
    values = subset["pearson_residual"].to_numpy()
    axis.bar(subset["label"], values, color=np.where(values >= 0, _RED, _GREEN))
    axis.axhline(0, color=_INK, linewidth=0.8)
    axis.tick_params(axis="x", labelsize=7)
    return figure


def detection_power_figure(table: pd.DataFrame) -> Figure:
    _require_columns(table, "pocket_probability", "estimated_power", "alpha")
    figure, axis = _axes(
        "Detection power for a single-pocket bias",
        "Selected pocket probability",
        "Rejection probability",
    )
    axis.plot(
        table["pocket_probability"],
        table["estimated_power"],
        color=_GREEN,
        marker="o",
        linewidth=2,
        label="Estimated power",
    )
    axis.axhline(float(table["alpha"].iloc[0]), color=_RED, linestyle="--", label="Alpha")
    axis.set_ylim(0, 1.02)
    axis.legend(frameon=False)
    return figure


def bankroll_risk_figure(table: pd.DataFrame) -> Figure:
    _require_columns(
        table,
        "strategy",
        "terminal_median",
        "terminal_percentile_5",
        "terminal_percentile_95",
    )
    figure, axis = _axes(
        "Terminal bankroll: median and 90% simulation interval",
        "Strategy",
        "Terminal bankroll",
    )
    x = np.arange(len(table))
    median = table["terminal_median"].to_numpy()
    low = table["terminal_percentile_5"].to_numpy()
    high = table["terminal_percentile_95"].to_numpy()
    axis.errorbar(
        x,
        median,
        yerr=np.vstack((median - low, high - median)),
        fmt="o",
        color=_INK,
        ecolor=_GOLD,
        capsize=5,
        linewidth=2,
    )
    axis.set_xticks(x, table["strategy"], rotation=18)
    return figure


def sequential_evidence_figure(table: pd.DataFrame) -> Figure:
    """Plot the simple-null/simple-alternative e-value path on a log scale."""

    _require_columns(table, "spin", "e_value", "e_value_threshold", "scenario")
    subset = table.loc[table["scenario"] == "fair_null"].sort_values("spin")
    if subset.empty:
        raise ValueError("sequential evidence requires a fair_null scenario.")
    figure, axis = _axes(
        "Sequential likelihood-ratio evidence under a fair wheel",
        "Spin",
        "E-value (log scale)",
    )
    finite_display = np.maximum(subset["e_value"].to_numpy(dtype=float), np.finfo(float).tiny)
    axis.semilogy(subset["spin"], finite_display, color=_BLUE, linewidth=1.6, label="Fair showcase path")
    threshold = float(subset["e_value_threshold"].iloc[0])
    axis.axhline(threshold, color=_RED, linestyle="--", linewidth=1.2, label="Evidence threshold")
    first_crossing = int(subset["first_crossing"].iloc[0]) if "first_crossing" in subset else 0
    if first_crossing > 0:
        crossing = subset.loc[subset["spin"] == first_crossing].iloc[0]
        axis.scatter([first_crossing], [crossing["e_value"]], color=_RED, zorder=3, label="First crossing")
    axis.legend(frameon=False, loc="best")
    return figure


def change_point_cusum_figure(table: pd.DataFrame) -> Figure:
    """Plot fair and changed CUSUM showcase paths with decision references."""

    _require_columns(
        table,
        "scenario",
        "spin",
        "cusum_score",
        "cusum_threshold",
        "true_change_spin",
        "first_alarm",
    )
    figure, axis = _axes(
        "Page CUSUM: fair versus changed showcase streams",
        "Spin",
        "CUSUM score",
    )
    colours = {"fair_null": _BLUE, "changed": _GREEN}
    for scenario, subset in table.groupby("scenario", sort=False):
        subset = subset.sort_values("spin")
        colour = colours["fair_null"] if scenario == "fair_null" else colours["changed"]
        label = "Fair null path" if scenario == "fair_null" else "Changed path"
        axis.plot(subset["spin"], subset["cusum_score"], color=colour, linewidth=1.5, label=label)
        first_alarm = int(subset["first_alarm"].iloc[0])
        if first_alarm > 0:
            alarm = subset.loc[subset["spin"] == first_alarm].iloc[0]
            axis.scatter([first_alarm], [alarm["cusum_score"]], color=_RED, marker="o", zorder=4)
            axis.annotate("First alarm", (first_alarm, alarm["cusum_score"]), xytext=(6, 8), textcoords="offset points", fontsize=8, color=_INK)
    threshold = float(table["cusum_threshold"].iloc[0])
    axis.axhline(threshold, color=_RED, linestyle="--", linewidth=1.2, label="CUSUM threshold")
    changed = table.loc[table["true_change_spin"] > 0]
    if not changed.empty:
        change_spin = int(changed["true_change_spin"].iloc[0])
        axis.axvline(change_spin, color=_GOLD, linestyle=":", linewidth=1.5, label="True change")
    axis.legend(frameon=False, loc="upper left")
    return figure


def posterior_edge_figure(table: pd.DataFrame) -> Figure:
    """Show the teaching-sample posterior beside its break-even probability."""

    _require_columns(
        table,
        "posterior_alpha",
        "posterior_beta",
        "break_even_probability",
        "credible_interval_lower",
        "credible_interval_upper",
    )
    row = table.iloc[0]
    right = min(
        1.0,
        max(
            float(row["credible_interval_upper"]) * 1.35,
            float(row["break_even_probability"]) * 1.7,
            float(row["posterior_mean"]) * 1.4,
        ),
    )
    x = np.linspace(0.0, right, 500)
    density = scipy.stats.beta.pdf(x, float(row["posterior_alpha"]), float(row["posterior_beta"]))
    figure, axis = _axes(
        "Posterior probability for the biased teaching sample",
        "Pocket probability",
        "Posterior density",
    )
    axis.plot(x, density, color=_BLUE, linewidth=2, label="Beta posterior")
    interval = (x >= float(row["credible_interval_lower"])) & (x <= float(row["credible_interval_upper"]))
    axis.fill_between(x[interval], density[interval], color=_BLUE, alpha=0.16, label="95% credible interval")
    axis.axvline(float(row["break_even_probability"]), color=_RED, linestyle="--", linewidth=1.3, label="Break-even probability")
    axis.axvline(float(row["posterior_mean"]), color=_GREEN, linestyle=":", linewidth=1.5, label="Posterior mean")
    axis.legend(frameon=False, loc="best")
    return figure


def risk_frontier_figure(table: pd.DataFrame) -> Figure:
    """Compare expected log growth across explicitly labelled Kelly fractions."""

    _require_columns(
        table,
        "kelly_fraction_multiplier",
        "strategy",
        "expected_log_growth",
        "terminal_cvar_shortfall",
    )
    ordered = table.sort_values("kelly_fraction_multiplier")
    fractions = ordered["kelly_fraction_multiplier"].to_numpy(dtype=float)
    growth = ordered["expected_log_growth"].to_numpy(dtype=float)
    finite = np.isfinite(growth)
    plot_growth = growth.copy()
    if finite.any():
        fallback = float(np.min(growth[finite]) - max(0.02, abs(np.min(growth[finite])) * 0.1))
    else:
        fallback = -1.0
    plot_growth[~finite] = fallback
    figure, axis = _axes(
        "Kelly risk frontier under common random outcomes",
        "Kelly fraction multiplier",
        "Expected log growth",
    )
    axis.plot(fractions, plot_growth, color=_GREEN, marker="o", linewidth=2)
    axis.margins(x=0.12)
    for fraction, value, strategy, is_finite in zip(
        fractions, plot_growth, ordered["strategy"], finite, strict=True
    ):
        label = f"{strategy.replace('_', ' ')} ({fraction:.0%})"
        if not is_finite:
            label += "; -inf"
        axis.annotate(label, (fraction, value), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8, color=_INK)
    axis.set_xticks(fractions, [f"{fraction:.0%}" for fraction in fractions])
    axis.axhline(0.0, color=_INK, linewidth=0.8)
    return figure


def publication_figures(bundle: "AnalysisBundle") -> Mapping[str, Figure]:
    return {
        "01_wheel_layout.png": wheel_layout_figure(),
        "02_house_edge_comparison.png": house_edge_figure(bundle.house_edges),
        "03_lln_convergence.png": lln_convergence_figure(bundle.lln_convergence),
        "04_bias_residuals.png": residual_figure(bundle.observed_residuals),
        "05_detection_power.png": detection_power_figure(bundle.detection_power),
        "06_bankroll_risk.png": bankroll_risk_figure(bundle.strategy_risk),
        "07_sequential_evidence.png": sequential_evidence_figure(bundle.sequential_evidence),
        "08_change_point_cusum.png": change_point_cusum_figure(bundle.change_point_results),
        "09_posterior_edge.png": posterior_edge_figure(bundle.posterior_edge),
        "10_risk_frontier.png": risk_frontier_figure(bundle.risk_frontier),
    }


def _require_columns(table: pd.DataFrame, *columns: str) -> None:
    if not isinstance(table, pd.DataFrame):
        raise TypeError("figure input must be a pandas DataFrame.")
    missing = set(columns) - set(table.columns)
    if missing:
        raise ValueError(f"figure input is missing columns: {sorted(missing)}")
