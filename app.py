"""Streamlit renderer for the Roulette Analytics Lab."""

import os
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
sys.path.insert(0, str(ROOT / "src"))

from roulette_lab.bets import BetKind  # noqa: E402
from roulette_lab.dashboard import (  # noqa: E402
    DashboardInputs,
    build_bankroll_view,
    build_fairness_view,
    build_wheel_view,
)
from roulette_lab.io import read_spin_csv  # noqa: E402
from roulette_lab.wheels import WheelKind, make_fair_wheel  # noqa: E402


st.set_page_config(
    page_title="Roulette Analytics Lab",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root { --ink:#17211d; --green:#12634f; --red:#bd3c3c; --gold:#a77b25; --line:#cdd4cc; }
    html, body, [class*="css"] { font-family: "Avenir Next", Avenir, "Segoe UI", sans-serif; }
    .stApp { background: #f4f6f2; color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(244,246,242,.96); }
    [data-testid="stSidebar"] { background: #e8ece7; border-right: 1px solid var(--line); }
    [data-testid="stMetric"] { border-top: 3px solid var(--green); padding-top: .8rem; }
    [data-testid="stMetricValue"] { font-size: 1.65rem; letter-spacing: 0; }
    .lab-title { border-bottom: 1px solid var(--line); padding: .6rem 0 1rem; margin-bottom: 1rem; }
    .lab-title h1 { font-size: 2.2rem; line-height: 1.12; letter-spacing: 0; margin: 0; color: var(--ink); }
    .lab-title p { margin: .45rem 0 0; color: #4d5953; max-width: 72ch; }
    .scenario-note { border-left: 4px solid var(--gold); padding: .65rem .8rem; background: #f0eee7; }
    .risk-note { border-left-color: var(--red); background: #f5eaea; }
    .method-band { border-top: 1px solid var(--line); padding: 1rem 0; }
    .stButton button, .stDownloadButton button { border-radius: 4px; min-height: 2.5rem; }
    [data-baseweb="tab-list"] { gap: 1.6rem; border-bottom: 1px solid var(--line); }
    [data-baseweb="tab"] { padding-left: 0; padding-right: 0; }
    @media (max-width: 760px) {
      .lab-title h1 { font-size: 1.7rem; }
      [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _selection_options(kind: BetKind, wheel_kind: WheelKind) -> list[tuple[str, ...]]:
    zeroes = [("0",)] if wheel_kind is WheelKind.EUROPEAN else [("0",), ("00",)]
    rows = [tuple(str(value) for value in range(start, start + 3)) for start in range(1, 37, 3)]
    if kind is BetKind.STRAIGHT:
        return zeroes + [(str(value),) for value in range(1, 37)]
    if kind is BetKind.SPLIT:
        horizontal = [(row[index], row[index + 1]) for row in rows for index in range(2)]
        vertical = [(str(value), str(value + 3)) for value in range(1, 34)]
        return horizontal + vertical
    if kind is BetKind.STREET:
        return rows
    if kind is BetKind.CORNER:
        return [
            (str(start), str(start + 1), str(start + 3), str(start + 4))
            for start in range(1, 34, 3)
            for _ in (0,)
        ] + [
            (str(start + 1), str(start + 2), str(start + 4), str(start + 5))
            for start in range(1, 34, 3)
        ]
    if kind is BetKind.SIX_LINE:
        return [rows[index] + rows[index + 1] for index in range(11)]
    if kind is BetKind.DOZEN:
        return [tuple(str(value) for value in range(start, start + 12)) for start in (1, 13, 25)]
    if kind is BetKind.COLUMN:
        return [tuple(str(value) for value in range(start, 37, 3)) for start in (1, 2, 3)]
    return [()]


def _format_selection(selection: tuple[str, ...]) -> str:
    return "Derived standard coverage" if not selection else " / ".join(selection)


def _plotly_layout(figure):
    figure.update_layout(
        paper_bgcolor="#f4f6f2",
        plot_bgcolor="#f4f6f2",
        font={"family": "Avenir Next, Segoe UI, sans-serif", "color": "#17211d"},
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        legend_title_text="",
    )
    return figure


st.markdown(
    """
    <div class="lab-title">
      <h1>Roulette Analytics Lab</h1>
      <p>Bias detection, exact bet economics and bankroll risk in one reproducible statistical workspace.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Scenario")
    wheel_kind = WheelKind(st.selectbox("Wheel", [kind.value for kind in WheelKind]))
    rule = st.selectbox("Rule", ["standard", "la_partage", "en_prison"])
    bet_kind = BetKind(st.selectbox("Bet", [kind.value for kind in BetKind]))
    choices = _selection_options(bet_kind, wheel_kind)
    selection = st.selectbox("Selection", choices, format_func=_format_selection)
    fair_probability = 1 / (37 if wheel_kind is WheelKind.EUROPEAN else 38)
    wheel_labels = make_fair_wheel(wheel_kind).labels
    bias_label = st.selectbox("Biased pocket", wheel_labels, index=wheel_labels.index("17"))
    bias_probability = st.slider(
        "Pocket probability", 0.0, 0.12, float(fair_probability), 0.001, format="%.3f"
    )
    alpha = st.select_slider("Significance level", options=[0.01, 0.025, 0.05, 0.10], value=0.05)
    seed = st.number_input("Random seed", min_value=0, value=20260912, step=1)

    st.subheader("Bankroll")
    initial = st.number_input("Initial bankroll", min_value=10.0, value=1000.0, step=10.0)
    base_stake = st.number_input("Base stake", min_value=1.0, value=10.0, step=1.0)
    stop_loss = st.number_input("Stop-loss", min_value=0.0, value=500.0, step=10.0)
    take_profit = st.number_input("Take-profit", min_value=1.0, value=2000.0, step=10.0)
    paths = st.number_input("Simulation paths", min_value=10, max_value=10000, value=500, step=10)
    spins = st.number_input("Spins per path", min_value=1, max_value=5000, value=200, step=10)
    strategy = st.selectbox(
        "Strategy",
        ["flat", "martingale", "reverse_martingale", "full_kelly", "half_kelly", "quarter_kelly"],
    )
    estimated_probability = st.number_input(
        "Estimated win probability", min_value=0.0, max_value=1.0, value=float(fair_probability), format="%.5f"
    )
    odds_mode = st.radio("Odds", ["Casino standard", "Custom hypothetical"], horizontal=False)
    custom_odds = None
    if odds_mode == "Custom hypothetical":
        custom_odds = st.number_input("Custom net odds", min_value=0.01, value=40.0, step=1.0)

try:
    inputs = DashboardInputs(
        wheel_kind=wheel_kind.value,
        rule=rule,
        bet_kind=bet_kind.value,
        selection=selection,
        initial_bankroll=initial,
        base_stake=base_stake,
        stop_loss=stop_loss,
        take_profit=take_profit,
        paths=int(paths),
        spins=int(spins),
        strategy=strategy,
        estimated_win_probability=estimated_probability,
        bias_label=bias_label,
        bias_probability=bias_probability,
        alpha=alpha,
        simulations=2000,
        seed=int(seed),
        odds_mode=odds_mode,
        custom_net_odds=custom_odds,
    )
except (TypeError, ValueError) as error:
    st.error(str(error))
    st.stop()

wheel_tab, fairness_tab, bankroll_tab, methods_tab = st.tabs(
    ["Wheel & Bets", "Fairness Lab", "Bankroll Simulator", "Methods & Limits"]
)

with wheel_tab:
    try:
        wheel_view = build_wheel_view(inputs)
    except (TypeError, ValueError) as error:
        st.error(str(error))
    else:
        first, second, third = st.columns(3)
        first.metric("Standard house edge", f"{100 * wheel_view.standard_house_edge:.2f}%")
        second.metric("Expected return per unit", f"{wheel_view.standard_expected_net_return:.4f}")
        third.metric("Simulation payout", wheel_view.simulation_payout_label.rsplit(" ", 1)[-1])
        st.markdown(f'<div class="scenario-note">{wheel_view.scenario_notice}</div>', unsafe_allow_html=True)
        colors = {"red": "#bd3c3c", "black": "#17211d", "green": "#12634f"}
        figure = px.bar(
            wheel_view.probabilities,
            x="label",
            y="probability",
            color="colour",
            color_discrete_map=colors,
            title="Pocket probability model",
        )
        st.plotly_chart(_plotly_layout(figure), width="stretch")
        st.download_button(
            "Download probability table",
            wheel_view.probabilities.to_csv(index=False),
            "wheel_probabilities.csv",
            "text/csv",
        )

with fairness_tab:
    source = st.radio("Data source", ["Biased example", "Unbiased example", "Upload CSV"], horizontal=True)
    upload = st.file_uploader("Spin history", type="csv") if source == "Upload CSV" else None
    if source == "Upload CSV" and upload is None:
        st.info("Upload a CSV with exactly two columns: spin,pocket.")
    else:
        path = ROOT / "data" / ("example_biased_spins.csv" if source == "Biased example" else "example_unbiased_spins.csv")
        try:
            dataset = read_spin_csv(upload if upload is not None else path, make_fair_wheel(wheel_kind))
            with st.spinner("Running global and selection-aware tests..."):
                fairness = build_fairness_view(dataset, inputs)
        except (TypeError, ValueError, UnicodeError) as error:
            st.error(f"CSV validation failed: {error}")
        else:
            if fairness.sample_warning:
                st.warning(fairness.sample_warning)
            st.markdown(f'<div class="scenario-note risk-note">{fairness.selection_warning}</div>', unsafe_allow_html=True)
            metrics = st.columns(4)
            metrics[0].metric("Hottest pocket", fairness.hottest_label)
            metrics[1].metric("Global MC p-value", f"{fairness.monte_carlo_global_p_value:.4g}")
            metrics[2].metric("Naive p-value", f"{fairness.naive_p_value:.4g}")
            metrics[3].metric("Family-wise p-value", f"{fairness.familywise_p_value:.4g}")
            residual_chart = px.bar(
                fairness.counts,
                x="label",
                y="residual",
                color="residual",
                color_continuous_scale=["#12634f", "#e8ece7", "#bd3c3c"],
                color_continuous_midpoint=0,
                title="Pearson residuals by pocket",
            )
            st.plotly_chart(_plotly_layout(residual_chart), width="stretch")
            st.download_button(
                "Download test table", fairness.counts.to_csv(index=False), "fairness_counts.csv", "text/csv"
            )

with bankroll_tab:
    try:
        with st.spinner("Simulating bankroll paths..."):
            bankroll = build_bankroll_view(inputs)
    except (TypeError, ValueError) as error:
        st.error(str(error))
    else:
        if bankroll.no_edge_message:
            st.info(bankroll.no_edge_message)
        st.markdown(f'<div class="scenario-note">{bankroll.scenario_notice}</div>', unsafe_allow_html=True)
        metrics = st.columns(4)
        metrics[0].metric("Terminal median", f"{bankroll.risk.terminal_median:,.0f}")
        metrics[1].metric("Loss probability", f"{100 * bankroll.risk.probability_of_loss:.1f}%")
        metrics[2].metric("Ruin probability", f"{100 * bankroll.risk.probability_of_ruin:.1f}%")
        metrics[3].metric("Expected max drawdown", f"{100 * bankroll.risk.expected_maximum_drawdown:.1f}%")
        shown = bankroll.equity_data[: min(40, len(bankroll.equity_data))]
        path_frame = pd.DataFrame(shown.T)
        path_frame["spin"] = range(len(path_frame))
        long_paths = path_frame.melt(id_vars="spin", var_name="path", value_name="equity")
        path_chart = px.line(long_paths, x="spin", y="equity", color="path", title="Marked-to-model bankroll equity paths")
        path_chart.update_traces(line={"width": 1}, opacity=0.55)
        path_chart.update_layout(showlegend=False)
        st.plotly_chart(_plotly_layout(path_chart), width="stretch")
        st.download_button(
            "Download risk summary", bankroll.summary_table.to_csv(index=False), "bankroll_risk.csv", "text/csv"
        )

with methods_tab:
    st.subheader("Decision rules")
    st.markdown(
        r"""
        <div class="method-band"><strong>Expected net return</strong></div>

        $$E[X]=p\,b-(1-p)$$

        The payout multiple is fixed by the typed casino bet. Custom odds are isolated as a hypothetical simulation input.

        <div class="method-band"><strong>Selection-aware bias test</strong></div>

        The global maximum-count p-value compares the observed maximum with maxima from complete multinomial samples. A binomial test on the hottest observed pocket is reported only as the naive reference.

        <div class="method-band"><strong>Kelly sizing</strong></div>

        $$f^*=\max\left(0,\frac{bp-(1-p)}{b}\right)$$

        Kelly is optimal for expected logarithmic growth only when the probability and payout model are correct. It does not guarantee profit.

        <div class="method-band"><strong>Limits</strong></div>

        Simulations show model-conditioned risk, not evidence that a live wheel is biased. A candidate pocket should be estimated on one sample and evaluated on separate validation spins. Casino rules, table limits and implementation details vary by venue.
        """,
        unsafe_allow_html=True,
    )
