"""Evidence Cockpit renderer for the Roulette Analytics Lab."""

from __future__ import annotations

import base64
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import scipy.stats
import streamlit as st


ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
sys.path.insert(0, str(ROOT / "src"))

from roulette_lab.bankroll import StrategyKind  # noqa: E402
from roulette_lab.bets import BetKind, SpecialRule, make_standard_bet  # noqa: E402
from roulette_lab.dashboard import (  # noqa: E402
    DashboardInputs,
    DecisionRiskView,
    LiveExperimentView,
    build_decision_risk_view,
    build_fairness_view,
    build_live_experiment_view,
    build_wheel_view,
)
from roulette_lab.experiment import advance_experiment, new_experiment, reset_experiment  # noqa: E402
from roulette_lab.io import read_spin_csv  # noqa: E402
from roulette_lab.roulette_component import colours_for_rotor, rotor_order_for_labels, roulette_wheel_html  # noqa: E402
from roulette_lab.wheels import WheelKind, make_fair_wheel  # noqa: E402


CRIMSON = "#D32842"
INK = "#171816"
PAPER = "#F7F7F4"
SILVER = "#B9BAB4"
MUTED = "#646660"

st.set_page_config(page_title="Roulette Analytics Lab", page_icon="R", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
    :root { --ink:#171816; --paper:#F7F7F4; --crimson:#D32842; --silver:#B9BAB4; --muted:#646660; --line:#D6D6D0; }
    html, body, [class*="css"] { font-family:"Avenir Next", Avenir, "Segoe UI", sans-serif; }
    .stApp { background:var(--paper); color:var(--ink); }
    [data-testid="stHeader"] { background:rgba(247,247,244,.96); border-bottom:1px solid var(--line); }
    [data-testid="stSidebar"] { background:#eeeee9; border-right:1px solid var(--line); }
    [data-testid="stMetric"] { min-height:88px; border-top:2px solid var(--ink); padding:.7rem 0 .2rem; }
    [data-testid="stMetricValue"] { font-size:1.62rem; letter-spacing:0; }
    [data-baseweb="tab-list"] { gap:1.4rem; border-bottom:1px solid var(--line); }
    [data-baseweb="tab"] { padding:.75rem 0; font-weight:650; color:var(--muted); }
    [aria-selected="true"][data-baseweb="tab"] { color:var(--crimson); border-bottom:2px solid var(--crimson); }
    .cockpit-title { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:1.5rem; align-items:end; border-bottom:2px solid var(--ink); padding:.8rem 0 1rem; margin:0 0 .6rem; }
    .cockpit-title h1 { margin:0; font-size:clamp(1.75rem,3vw,2.7rem); line-height:1; letter-spacing:0; }
    .cockpit-title p { max-width:65ch; margin:.55rem 0 0; color:var(--muted); line-height:1.45; }
    .cockpit-title .state { color:var(--crimson); font-size:.85rem; font-weight:700; white-space:nowrap; }
    .workspace-heading { margin:1.3rem 0 .2rem; font-size:1.12rem; line-height:1.2; }
    .workspace-note { color:var(--muted); margin:0 0 1rem; max-width:74ch; line-height:1.45; }
    .experiment-stage { background:var(--ink); color:var(--paper); padding:1.1rem; margin:1rem 0; border-top:3px solid var(--crimson); }
    .experiment-stage h2 { color:var(--paper); margin:0; font-size:1.1rem; }
    .experiment-stage p { color:#d7d8d2; margin:.35rem 0 0; }
    .rule-note { border-left:3px solid var(--crimson); padding:.55rem .75rem; margin:.8rem 0; background:#f0f0ec; color:#343530; }
    .quiet-rule { border-top:1px solid var(--line); margin:1.2rem 0 .7rem; }
    .stButton button, .stDownloadButton button { border-radius:3px; min-height:2.4rem; border:1px solid var(--ink); background:var(--paper); color:var(--ink); font-weight:650; }
    .stButton button[kind="primary"] { border-color:var(--crimson); background:var(--crimson); color:#fff; }
    .stButton button:active, .stDownloadButton button:active { transform:translateY(1px) scale(.99); }
    [data-testid="stPlotlyChart"] { border-top:1px solid var(--line); padding-top:.4rem; }
    [data-testid="stExpander"] { border:0; border-top:1px solid var(--line); border-radius:0; }
    @media (max-width:760px) {
      .cockpit-title { display:block; }
      .cockpit-title .state { display:block; margin-top:.7rem; }
      .cockpit-title h1, .cockpit-title p, .workspace-note, .rule-note { white-space: normal !important; overflow-wrap: anywhere; }
      [data-baseweb="tab-list"] { overflow-x: auto; gap:1rem; }
      [data-baseweb="tab"] { flex:0 0 auto; }
      [data-testid="stHorizontalBlock"] { flex-wrap:wrap; }
      [data-testid="stMetricValue"] { font-size:1.32rem; }
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
        return [(row[index], row[index + 1]) for row in rows for index in range(2)] + [(str(value), str(value + 3)) for value in range(1, 34)]
    if kind is BetKind.STREET:
        return rows
    if kind is BetKind.CORNER:
        return [(str(start), str(start + 1), str(start + 3), str(start + 4)) for start in range(1, 34, 3)] + [(str(start + 1), str(start + 2), str(start + 4), str(start + 5)) for start in range(1, 34, 3)]
    if kind is BetKind.SIX_LINE:
        return [rows[index] + rows[index + 1] for index in range(11)]
    if kind is BetKind.DOZEN:
        return [tuple(str(value) for value in range(start, start + 12)) for start in (1, 13, 25)]
    if kind is BetKind.COLUMN:
        return [tuple(str(value) for value in range(start, 37, 3)) for start in (1, 2, 3)]
    return [()]


def _format_selection(selection: tuple[str, ...]) -> str:
    return "Derived standard coverage" if not selection else " / ".join(selection)


def _figure(title: str, height: int = 310) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        title={"text": title, "font": {"size": 15, "color": INK}}, height=height,
        paper_bgcolor=PAPER, plot_bgcolor=PAPER, font={"family": "Avenir Next, Segoe UI, sans-serif", "color": INK},
        margin={"l": 35, "r": 18, "t": 46, "b": 35}, showlegend=True,
        legend={"orientation": "h", "y": 1.08, "x": 0}, uirevision="evidence-cockpit",
    )
    figure.update_xaxes(showgrid=False, zeroline=False, linecolor=SILVER)
    figure.update_yaxes(gridcolor="#E2E2DC", zeroline=False, linecolor=SILVER)
    return figure


def _plotly(figure: go.Figure) -> None:
    st.plotly_chart(figure, width="stretch", config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]})


def _render_wheel_html(markup: str) -> None:
    source = base64.b64encode(markup.encode("utf-8")).decode("ascii")
    st.iframe(f"data:text/html;base64,{source}", height=510)


def _scenario_inputs() -> DashboardInputs:
    with st.sidebar:
        st.header("Experiment controls")
        wheel_kind = WheelKind(st.selectbox("Wheel", [kind.value for kind in WheelKind]))
        rule = st.selectbox("Rule", [rule.value for rule in SpecialRule])
        bet_kind = BetKind(st.selectbox("Bet", [kind.value for kind in BetKind]))
        selections = _selection_options(bet_kind, wheel_kind)
        default_selection = ("17",) if ("17",) in selections else selections[0]
        selection = st.selectbox("Selection", selections, index=selections.index(default_selection), format_func=_format_selection)
        wheel_labels = make_fair_wheel(wheel_kind).labels
        st.divider()
        initial = st.number_input("Initial bankroll", min_value=10.0, value=1000.0, step=10.0)
        stake = st.number_input("Live stake", min_value=1.0, value=10.0, step=1.0)
        stop_loss = st.number_input("Stop-loss", min_value=0.0, value=500.0, step=10.0)
        take_profit = st.number_input("Take-profit", min_value=100.0, value=2000.0, step=10.0)
        st.divider()
        target_probability = st.number_input("Declared alternative probability", min_value=0.01, max_value=0.99, value=0.60, step=0.01, format="%.2f")
        cusum_threshold = st.number_input("CUSUM threshold", min_value=0.1, value=3.0, step=0.1)
        prior_strength = st.number_input("Posterior prior strength", min_value=0.1, value=37.0, step=1.0)
        seed = st.number_input("Random seed", min_value=0, value=20260912, step=1)
        with st.expander("Simulation controls"):
            paths = st.number_input("Simulation paths", min_value=20, max_value=10000, value=500, step=20)
            spins = st.number_input("Spins per path", min_value=1, max_value=5000, value=200, step=10)
            strategy = st.selectbox("Reference strategy", [strategy.value for strategy in StrategyKind])
            odds_mode = st.radio("Odds", ["Casino standard", "Custom hypothetical"])
            custom_odds = st.number_input("Custom net odds", min_value=0.01, value=40.0, step=1.0) if odds_mode == "Custom hypothetical" else None
    return DashboardInputs(
        wheel_kind=wheel_kind.value, rule=rule, bet_kind=bet_kind.value, selection=selection,
        initial_bankroll=initial, base_stake=stake, live_stake=stake, stop_loss=stop_loss, take_profit=take_profit,
        paths=int(paths), spins=int(spins), strategy=strategy, estimated_win_probability=None,
        bias_label="17", bias_probability=1 / len(wheel_labels), alpha=0.05, simulations=2000, seed=int(seed),
        odds_mode=odds_mode, custom_net_odds=custom_odds, target_probability=target_probability,
        cusum_threshold=cusum_threshold, posterior_prior_strength=prior_strength,
    )


def _experiment_state(inputs: DashboardInputs):
    signature = (inputs.seed, inputs.initial_bankroll, inputs.wheel_kind, inputs.rule, inputs.bet_kind, inputs.selection)
    if st.session_state.get("experiment_signature") != signature:
        st.session_state.experiment_state = new_experiment(inputs.seed, inputs.initial_bankroll)
        st.session_state.experiment_signature = signature
    return st.session_state.experiment_state


@st.cache_data(show_spinner=False)
def _cached_decision_risk(state, inputs: DashboardInputs) -> DecisionRiskView:
    return build_decision_risk_view(state, inputs)


def _render_live(view: LiveExperimentView, inputs: DashboardInputs, state) -> None:
    st.markdown('<div class="experiment-stage"><h2>Live rotor</h2><p>The result is drawn in Python. The wheel only settles on that result.</p></div>', unsafe_allow_html=True)
    wheel = make_fair_wheel(WheelKind(inputs.wheel_kind))
    rotor = rotor_order_for_labels(wheel.labels)
    _render_wheel_html(roulette_wheel_html(rotor, colours_for_rotor(rotor), view.result, view.sample_size, False))
    controls = st.columns([1, 1, 1, 1, 1, 1])
    requests = [("Spin once", 1), ("Batch 10", 10), ("Batch 50", 50), ("Batch 100", 100)]
    for column, (label, count) in zip(controls[:4], requests, strict=True):
        if column.button(label, key=f"spin-{count}", type="primary" if count == 1 else "secondary", width="stretch"):
            bet = make_standard_bet(BetKind(inputs.bet_kind), inputs.selection, wheel)
            st.session_state.experiment_state = advance_experiment(state, wheel, bet, SpecialRule(inputs.rule), inputs.live_stake, count)
            st.rerun()
    history = pd.DataFrame({"spin": np.arange(1, view.sample_size + 1), "pocket": state.history})
    controls[4].download_button("Download history", history.to_csv(index=False), "roulette_history.csv", "text/csv", width="stretch")
    if controls[5].button("Reset", width="stretch"):
        st.session_state.experiment_state = reset_experiment(state)
        st.rerun()
    if view.empty_message:
        st.info(view.empty_message)
        return
    metrics = st.columns(4)
    metrics[0].metric("Recorded spins", view.sample_size)
    metrics[1].metric("Selected hits", view.hits)
    metrics[2].metric("Current bankroll", f"{view.bankroll:,.0f}")
    metrics[3].metric("Posterior positive edge", f"{100 * view.posterior.probability_positive_edge:.1f}%")
    x = np.arange(1, view.sample_size + 1)
    frequency = _figure("Running selected-bet frequency and posterior band")
    frequency.add_trace(go.Scatter(x=x, y=view.posterior_band[0], line={"width": 0}, name="Lower band", hoverinfo="skip"))
    frequency.add_trace(go.Scatter(x=x, y=view.posterior_band[1], fill="tonexty", fillcolor="rgba(211,40,66,.16)", line={"width": 0}, name="Credible band", hovertemplate="%{y:.3f}"))
    frequency.add_trace(go.Scatter(x=x, y=view.running_frequency, line={"color": CRIMSON, "width": 2.5}, name="Running frequency"))
    frequency.add_hline(y=view.evidence.p0, line_dash="dot", line_color=MUTED, annotation_text="fair probability")
    _plotly(frequency)


def _render_evidence(view: LiveExperimentView) -> None:
    st.markdown('<h2 class="workspace-heading">Sequential evidence</h2><p class="workspace-note">The likelihood ratio and CUSUM both use the declared null and alternative. They do not turn a selected outcome into a prediction.</p>', unsafe_allow_html=True)
    if view.empty_message:
        st.info("Evidence paths appear after the first recorded spin.")
        return
    x = np.arange(1, view.sample_size + 1)
    e_value = _figure("E-value path")
    e_value.add_trace(go.Scatter(x=x, y=view.e_values, line={"color": CRIMSON, "width": 2.5}, name="E-value"))
    e_value.add_hline(y=view.evidence.evidence.threshold, line_dash="dash", line_color=INK, annotation_text="Decision threshold")
    e_value.update_yaxes(type="log", title="E-value")
    _plotly(e_value)
    cusum = _figure("CUSUM change diagnostic")
    cusum.add_trace(go.Scatter(x=x, y=view.cusum_scores, line={"color": INK, "width": 2.5}, name="CUSUM"))
    cusum.add_hline(y=view.evidence.cusum.threshold, line_dash="dash", line_color=CRIMSON, annotation_text="Alarm threshold")
    if view.evidence.cusum.first_alarm is not None:
        alarm = view.evidence.cusum.first_alarm
        cusum.add_trace(go.Scatter(x=[alarm], y=[view.cusum_scores[alarm - 1]], mode="markers", marker={"size": 10, "color": CRIMSON}, name="First alarm"))
    _plotly(cusum)
    if view.evidence.no_alarm_message:
        st.info(view.evidence.no_alarm_message)


def _render_risk(view: LiveExperimentView, state, inputs: DashboardInputs) -> None:
    st.markdown('<h2 class="workspace-heading">Posterior decision and forward risk</h2><p class="workspace-note">Run the simulation when the selected assumptions are ready. Common random numbers keep the Kelly comparison focused on stake sizing.</p>', unsafe_allow_html=True)
    posterior = view.posterior
    density_x = np.linspace(0.0001, min(0.9999, max(0.12, posterior.credible_interval[1] * 1.5)), 400)
    density = _figure("Posterior probability density")
    density.add_trace(go.Scatter(x=density_x, y=scipy.stats.beta.pdf(density_x, posterior.posterior_alpha, posterior.posterior_beta), fill="tozeroy", line={"color": CRIMSON, "width": 2.5}, fillcolor="rgba(211,40,66,.14)", name="Posterior"))
    density.add_vline(x=posterior.break_even_probability, line_dash="dash", line_color=INK, annotation_text="Break-even")
    _plotly(density)
    metrics = st.columns(4)
    metrics[0].metric("Posterior mean", f"{posterior.posterior_mean:.3%}")
    metrics[1].metric("Credible interval", f"{posterior.credible_interval[0]:.3%} to {posterior.credible_interval[1]:.3%}")
    metrics[2].metric("Conservative Kelly", f"{posterior.quantile_kelly:.2%}")
    metrics[3].metric("Predictive hits", f"{posterior.predictive_interval[0]} to {posterior.predictive_interval[1]}")
    with st.form("risk-simulation"):
        submitted = st.form_submit_button("Run risk simulation", type="primary")
    if submitted:
        with st.spinner("Simulating the requested bankroll paths..."):
            st.session_state.decision_risk = _cached_decision_risk(state, inputs)
            st.session_state.decision_signature = (state, inputs)
    decision = st.session_state.get("decision_risk") if st.session_state.get("decision_signature") == (state, inputs) else None
    if decision is None:
        st.info("No simulation is cached for these controls. Run risk simulation to inspect the frontier and fan chart.")
        return
    if decision.no_edge_message:
        st.warning(decision.no_edge_message)
    frontier = _figure("Kelly risk frontier")
    frontier.add_trace(go.Scatter(x=decision.frontier["expected_maximum_drawdown"], y=decision.frontier["expected_log_growth"], mode="lines+markers+text", text=["Quarter Kelly", "Half Kelly", "Full Kelly"], textposition="top center", marker={"color": CRIMSON, "size": 10}, line={"color": INK}, name="Strategy"))
    frontier.update_xaxes(title="Expected maximum drawdown")
    frontier.update_yaxes(title="Expected log growth")
    _plotly(frontier)
    paths = decision.bankroll.equity_data
    horizon = np.arange(paths.shape[1])
    fan = _figure("Bankroll fan chart")
    for quantile, label, colour, width in [(5, "5th percentile", MUTED, 1), (25, "25th percentile", SILVER, 1), (50, "Median", CRIMSON, 3), (75, "75th percentile", SILVER, 1), (95, "95th percentile", MUTED, 1)]:
        fan.add_trace(go.Scatter(x=horizon, y=np.percentile(paths, quantile, axis=0), name=label, line={"color": colour, "width": width, "dash": "dot" if quantile in {5, 95} else "solid"}))
    fan.update_xaxes(title="Spin")
    fan.update_yaxes(title="Equity")
    _plotly(fan)
    st.download_button("Download risk frontier", decision.frontier.to_csv(index=False), "risk_frontier.csv", "text/csv")


def _render_mechanics(inputs: DashboardInputs) -> None:
    st.markdown('<h2 class="workspace-heading">Wheel mechanics</h2><p class="workspace-note">The labelled probability vector remains statistical order. The visual rotor uses canonical physical order, validated against the same label set.</p>', unsafe_allow_html=True)
    wheel_view = build_wheel_view(inputs)
    wheel = make_fair_wheel(WheelKind(inputs.wheel_kind))
    rotor = rotor_order_for_labels(wheel.labels)
    _render_wheel_html(roulette_wheel_html(rotor, colours_for_rotor(rotor), None, 0, False))
    metrics = st.columns(3)
    metrics[0].metric("Standard house edge", f"{100 * wheel_view.standard_house_edge:.2f}%")
    metrics[1].metric("Expected return per unit", f"{wheel_view.standard_expected_net_return:.4f}")
    metrics[2].metric("Standard payout", wheel_view.standard_payout_label.rsplit(" ", 1)[-1])
    st.markdown(f'<div class="rule-note">{wheel_view.scenario_notice}</div>', unsafe_allow_html=True)
    distribution = _figure("Pocket probability model")
    palette = {"red": "#b62438", "black": "#22231f", "green": "#176046"}
    distribution.add_trace(go.Bar(x=wheel_view.probabilities["label"], y=wheel_view.probabilities["probability"], marker_color=[palette[colour] for colour in wheel_view.probabilities["colour"]], name="Pocket probability"))
    _plotly(distribution)
    st.download_button("Download probability table", wheel_view.probabilities.to_csv(index=False), "wheel_probabilities.csv", "text/csv")


def _render_methods(inputs: DashboardInputs) -> None:
    st.markdown('<h2 class="workspace-heading">Methods and limits</h2><p class="workspace-note">This lab makes model assumptions inspectable. It does not establish a casino edge or offer wagering advice.</p>', unsafe_allow_html=True)
    source = st.radio("Fairness data source", ["Biased example", "Unbiased example", "Upload CSV"], horizontal=True)
    upload = st.file_uploader("Spin history CSV", type="csv") if source == "Upload CSV" else None
    if source == "Upload CSV" and upload is None:
        st.info("Upload a CSV with exactly two columns: spin,pocket.")
    else:
        path = ROOT / "data" / ("example_biased_spins.csv" if source == "Biased example" else "example_unbiased_spins.csv")
        try:
            dataset = read_spin_csv(upload.getvalue() if upload else path, make_fair_wheel(WheelKind(inputs.wheel_kind)))
            fairness = build_fairness_view(dataset, inputs)
        except (TypeError, ValueError) as error:
            st.error(f"The data cannot be analysed: {error}")
        else:
            metrics = st.columns(3)
            metrics[0].metric("Chi-square", f"{fairness.chi_square_statistic:.2f}")
            metrics[1].metric("Monte Carlo global p", f"{fairness.monte_carlo_global_p_value:.4f}")
            metrics[2].metric("Family-wise p", f"{fairness.familywise_p_value:.4f}")
            st.markdown(f'<div class="rule-note">{fairness.selection_warning}</div>', unsafe_allow_html=True)
            if fairness.sample_warning:
                st.warning(fairness.sample_warning)
            st.dataframe(fairness.counts, width="stretch", hide_index=True)
    st.markdown('<div class="quiet-rule"></div><p class="workspace-note">Sequential statistics depend on the declared candidate probability. Posterior Kelly quantities are conditional sizing heuristics, not profit guarantees. Simulations are model-conditioned risk summaries.</p>', unsafe_allow_html=True)


try:
    inputs = _scenario_inputs()
except (TypeError, ValueError) as error:
    st.error(f"Invalid controls: {error}")
    st.stop()

state = _experiment_state(inputs)
try:
    live_view = build_live_experiment_view(state, inputs)
except (TypeError, ValueError) as error:
    st.error(f"The live experiment cannot be evaluated: {error}")
    st.stop()

status = "Awaiting observations" if live_view.sample_size == 0 else f"{live_view.sample_size} observations recorded"
st.markdown(f'<div class="cockpit-title"><div><h1>Roulette Analytics Lab</h1><p>A reproducible evidence workbench for wheel mechanics, sequential diagnostics, posterior decisions, and bankroll risk.</p></div><div class="state">{status}</div></div>', unsafe_allow_html=True)

live_tab, evidence_tab, risk_tab, mechanics_tab, methods_tab = st.tabs(
    ["Live Experiment", "Evidence", "Decision Risk", "Wheel Mechanics", "Methods"]
)
with live_tab:
    _render_live(live_view, inputs, state)
with evidence_tab:
    _render_evidence(live_view)
with risk_tab:
    _render_risk(live_view, state, inputs)
with mechanics_tab:
    _render_mechanics(inputs)
with methods_tab:
    _render_methods(inputs)
