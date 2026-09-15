from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from roulette_lab.analysis import AnalysisBundle, AnalysisConfig, run_full_analysis
from roulette_lab.figures import (
    EUROPEAN_WHEEL_ORDER,
    bankroll_risk_figure,
    detection_power_figure,
    house_edge_figure,
    lln_convergence_figure,
    publication_figures,
    residual_figure,
    risk_frontier_figure,
    wheel_layout_figure,
)


def test_wheel_figure_uses_physical_european_pocket_order():
    assert EUROPEAN_WHEEL_ORDER[:6] == ("0", "32", "15", "19", "4", "21")
    assert len(EUROPEAN_WHEEL_ORDER) == len(set(EUROPEAN_WHEEL_ORDER)) == 37


def test_default_analysis_contains_manual_evidence():
    bundle = run_full_analysis(AnalysisConfig.fast_test())

    assert isinstance(bundle, AnalysisBundle)
    assert {"european", "american", "la_partage", "en_prison"} <= set(
        bundle.house_edges["rule"]
    )
    assert {
        "flat",
        "martingale",
        "reverse_martingale",
        "full_kelly",
        "half_kelly",
    } <= set(bundle.strategy_risk["strategy"])
    assert {
        "naive_p_value",
        "bonferroni_p_value",
        "familywise_p_value",
    } <= set(bundle.bias_tests.columns)


def test_v2_bundle_contains_advanced_research_tables():
    bundle = run_full_analysis(AnalysisConfig.fast_test())

    assert {
        "spin",
        "e_value",
        "fixed_horizon_p_value",
    } <= set(bundle.sequential_evidence)
    assert {
        "scenario",
        "first_alarm",
        "detection_delay",
        "false_alarm_rate",
        "median_detection_delay",
        "monte_carlo_experiments",
        "true_change_spin",
    } <= set(bundle.change_point_results)
    assert {
        "posterior_mean",
        "probability_positive_edge",
        "quantile_kelly",
        "quantile_kelly_interpretation",
    } <= set(bundle.posterior_edge)
    assert {
        "kelly_fraction_multiplier",
        "terminal_cvar_shortfall",
        "expected_log_growth",
    } <= set(bundle.risk_frontier)
    assert len(AnalysisBundle.table_names()) == 11


def test_change_point_results_are_per_spin_paths_with_repeated_reliability_fields():
    bundle = run_full_analysis(AnalysisConfig.fast_test())
    table = bundle.change_point_results

    assert len(table) == 2_000
    assert set(table["scenario"]) == {"fair_null", "changed_at_500"}
    assert table.groupby("scenario")["spin"].nunique().to_dict() == {
        "changed_at_500": 1_000,
        "fair_null": 1_000,
    }
    assert table.groupby("scenario")["spin"].min().eq(1).all()
    assert table.groupby("scenario")["spin"].max().eq(1_000).all()
    repeated = (
        "false_alarm_rate",
        "median_detection_delay",
        "monte_carlo_experiments",
        "true_change_spin",
        "first_alarm",
        "detection_delay",
    )
    assert (table.groupby("scenario")[list(repeated)].nunique() == 1).all().all()
    changed = table.loc[table["scenario"] == "changed_at_500"]
    fair = table.loc[table["scenario"] == "fair_null"]
    assert changed["true_change_spin"].eq(500).all()
    assert fair["true_change_spin"].eq(0).all()
    assert table["false_alarm_rate"].between(0, 1).all()
    assert table["monte_carlo_experiments"].eq(250).all()


def test_default_analysis_is_reproducible():
    first = run_full_analysis(AnalysisConfig.fast_test())
    second = run_full_analysis(AnalysisConfig.fast_test())

    for name in AnalysisBundle.table_names():
        pd.testing.assert_frame_equal(getattr(first, name), getattr(second, name))


def test_analysis_config_rejects_invalid_simulation_controls():
    config = AnalysisConfig.fast_test()

    for changes in (
        {"alpha": 0.0},
        {"analysis_spins": 0},
        {"power_experiments": 0},
        {"bankroll_paths": True},
        {"bias_probability": 1.1},
    ):
        values = {field: getattr(config, field) for field in config.__dataclass_fields__}
        values.update(changes)
        try:
            AnalysisConfig(**values)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Invalid configuration accepted: {changes}")


def test_analysis_tables_are_tidy_finite_and_traceable():
    bundle = run_full_analysis(AnalysisConfig.fast_test())

    for name in AnalysisBundle.table_names():
        table = getattr(bundle, name)
        assert isinstance(table, pd.DataFrame)
        assert not table.empty
        assert not table.isna().any().any()
    assert set(bundle.bias_tests["dataset"]) == {"unbiased", "biased"}
    assert (bundle.detection_power["monte_carlo_standard_error"] >= 0).all()
    assert (bundle.strategy_risk["probability_of_ruin"].between(0, 1)).all()


def test_publication_figures_have_stable_dimensions():
    bundle = run_full_analysis(AnalysisConfig.fast_test())
    figures = (
        wheel_layout_figure(),
        house_edge_figure(bundle.house_edges),
        lln_convergence_figure(bundle.lln_convergence),
        residual_figure(bundle.observed_residuals),
        detection_power_figure(bundle.detection_power),
        bankroll_risk_figure(bundle.strategy_risk),
    )

    assert len(figures) == 6
    for figure in figures:
        width, height = figure.get_size_inches()
        assert width >= 8
        assert height >= 4.5
        plt.close(figure)


def test_publication_figures_include_v2_outputs():
    figures = publication_figures(run_full_analysis(AnalysisConfig.fast_test()))

    assert set(figures) == {
        "01_wheel_layout.png",
        "02_house_edge_comparison.png",
        "03_lln_convergence.png",
        "04_bias_residuals.png",
        "05_detection_power.png",
        "06_bankroll_risk.png",
        "07_sequential_evidence.png",
        "08_change_point_cusum.png",
        "09_posterior_edge.png",
        "10_risk_frontier.png",
    }
    for figure in figures.values():
        assert figure.axes
        assert any(axis.has_data() for axis in figure.axes)
        plt.close(figure)


def test_risk_frontier_keeps_space_for_the_quarter_kelly_annotation():
    figure = risk_frontier_figure(run_full_analysis(AnalysisConfig.fast_test()).risk_frontier)

    assert figure.axes[0].get_xlim()[0] <= 0.20
    plt.close(figure)


def test_analysis_entry_point_writes_all_tables_figures_and_summary(tmp_path):
    bundle = run_full_analysis(AnalysisConfig.fast_test())
    bundle.write(tmp_path)

    expected_tables = {f"{name}.csv" for name in AnalysisBundle.table_names()}
    assert expected_tables <= {path.name for path in (tmp_path / "tables").glob("*.csv")}
    assert len(list((tmp_path / "figures").glob("*.png"))) == 10
    summary = (tmp_path / "analysis_summary.md").read_text(encoding="utf-8")
    assert "Selection-aware" in summary
    assert "Kelly" in summary
    assert "not guaranteed profit" in summary


def test_analysis_csvs_ignore_platform_level_float_noise(tmp_path):
    reference = run_full_analysis(AnalysisConfig.fast_test())
    perturbed = run_full_analysis(AnalysisConfig.fast_test())
    column = "asymptotic_p_value"
    original = perturbed.bias_tests.loc[0, column]
    perturbed.bias_tests.loc[0, column] = np.nextafter(original, np.inf)

    reference.write(tmp_path / "reference")
    perturbed.write(tmp_path / "perturbed")

    reference_csv = (tmp_path / "reference" / "tables" / "bias_tests.csv").read_text()
    perturbed_csv = (tmp_path / "perturbed" / "tables" / "bias_tests.csv").read_text()
    assert reference_csv == perturbed_csv
