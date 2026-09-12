"""Publication figures for the roulette analysis bundle."""

from collections.abc import Mapping
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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


def publication_figures(bundle: "AnalysisBundle") -> Mapping[str, Figure]:
    return {
        "01_wheel_layout.png": wheel_layout_figure(),
        "02_house_edge_comparison.png": house_edge_figure(bundle.house_edges),
        "03_lln_convergence.png": lln_convergence_figure(bundle.lln_convergence),
        "04_bias_residuals.png": residual_figure(bundle.observed_residuals),
        "05_detection_power.png": detection_power_figure(bundle.detection_power),
        "06_bankroll_risk.png": bankroll_risk_figure(bundle.strategy_risk),
    }


def _require_columns(table: pd.DataFrame, *columns: str) -> None:
    if not isinstance(table, pd.DataFrame):
        raise TypeError("figure input must be a pandas DataFrame.")
    missing = set(columns) - set(table.columns)
    if missing:
        raise ValueError(f"figure input is missing columns: {sorted(missing)}")
