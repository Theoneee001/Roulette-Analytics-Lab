# Roulette Analytics Lab V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade Project 1 into a deeper, admissions-focused statistical portfolio with sequential inference, change-point diagnostics, posterior-aware decisions, lower-tail risk analysis, a polished live roulette experiment, and fully regenerated publications.

**Architecture:** Research functions stay independent of Streamlit and return frozen typed results. `analysis.py` remains the sole deterministic publication composer, while the app consumes the same tested functions through dashboard view models and an immutable experiment state. Every published claim is generated from code, checked by tests, and reused in the notebook, report, README, and interactive site.

**Tech Stack:** Python 3.12, NumPy, pandas, SciPy, Plotly, Matplotlib, Streamlit, ReportLab, nbformat/nbclient, pytest, HTML/CSS/JavaScript embedded through Streamlit components.

**Spec:** `docs/superpowers/specs/2026-09-14-roulette-analytics-lab-v2-design.md`

## Global Constraints

- Scope is Project 1 only; later portfolio projects do not affect this release gate.
- Preserve Kelly Criterion, chi-squared testing, random-walk simulation, adjustable bankroll/odds/stop-loss, live curves, technical blog, and complete README.
- Treat the group report as shared academic provenance and the V2 implementation as Jialiang Gong's independent extension.
- Use Python `>=3.12,<3.13` and the repository's existing dependency families.
- Use explicit `numpy.random.Generator` seeds for every published simulation.
- Do not claim a guaranteed edge, personalised gambling advice, live-casino prediction, or unrestricted sequential validity.
- Keep the English technical report between 4,500 and 5,000 prose words.
- Use the Evidence Cockpit C2 palette: `#171816`, `#F7F7F4`, `#D32842`, neutral silver greys, and green only for the zero pocket.
- Use rules, spacing, and background shifts instead of a repeated card grid.
- Respect `prefers-reduced-motion`; animation never chooses the roulette result.
- Keep the existing public repository and Streamlit URL.

---

### Task 1: Sequential Evidence and Change-Point Engine

**Files:**
- Create: `src/roulette_lab/sequential.py`
- Create: `tests/test_sequential.py`
- Modify: `src/roulette_lab/__init__.py`

**Interfaces:**
- Consumes: one-dimensional Boolean or zero/one observations and explicit `p0`, `p1`, `alpha`, and CUSUM threshold values.
- Produces: `SequentialEvidence`, `CUSUMResult`, `likelihood_ratio_path(...)`, and `cusum_change_detection(...)`.

- [ ] **Step 1: Write validation and likelihood-ratio tests**

```python
def test_all_hits_have_exact_log_likelihood_path():
    result = likelihood_ratio_path([1, 1, 1], p0=1 / 37, p1=0.06, alpha=0.05)
    expected = np.arange(1, 4) * np.log(0.06 / (1 / 37))
    np.testing.assert_allclose(result.log_likelihood_ratio, expected)
    np.testing.assert_allclose(result.e_values, np.exp(expected))
    assert result.threshold == pytest.approx(20.0)


@pytest.mark.parametrize("p0,p1", [(0, 0.1), (1, 0.9), (0.1, 0.1), (0.2, 0.1)])
def test_likelihood_ratio_rejects_invalid_probability_order(p0, p1):
    with pytest.raises(ValueError):
        likelihood_ratio_path([0, 1], p0=p0, p1=p1, alpha=0.05)
```

- [ ] **Step 2: Run the likelihood-ratio tests and verify RED**

Run: `.venv/bin/python -m pytest tests/test_sequential.py -q`

Expected: collection fails because `roulette_lab.sequential` does not exist.

- [ ] **Step 3: Implement the typed likelihood-ratio path**

```python
@dataclass(frozen=True, slots=True)
class SequentialEvidence:
    log_likelihood_ratio: NDArray[np.float64]
    e_values: NDArray[np.float64]
    threshold: float
    first_crossing: int | None
    p0: float
    p1: float
    alpha: float


def likelihood_ratio_path(observations, p0: float, p1: float, alpha: float) -> SequentialEvidence:
    values = _binary_observations(observations)
    p0, p1 = _ordered_probabilities(p0, p1)
    alpha = _open_unit(alpha, "alpha")
    increments = values * np.log(p1 / p0) + (1 - values) * np.log((1 - p1) / (1 - p0))
    log_path = np.cumsum(increments, dtype=float)
    e_values = np.exp(np.clip(log_path, -745.0, 709.0))
    threshold = 1.0 / alpha
    crossings = np.flatnonzero(e_values >= threshold)
    first = int(crossings[0] + 1) if crossings.size else None
    return SequentialEvidence(log_path, e_values, threshold, first, p0, p1, alpha)
```

- [ ] **Step 4: Add CUSUM reset, alarm, and no-alarm tests**

```python
def test_cusum_resets_negative_evidence_to_zero():
    result = cusum_change_detection([0, 0, 0], p0=1 / 37, p1=0.06, threshold=3.0)
    np.testing.assert_array_equal(result.scores, np.zeros(3))
    assert result.first_alarm is None


def test_cusum_reports_first_threshold_crossing():
    result = cusum_change_detection([1] * 20, p0=1 / 37, p1=0.06, threshold=3.0)
    expected = int(np.ceil(3.0 / np.log(0.06 / (1 / 37))))
    assert result.first_alarm == expected
    assert result.scores[expected - 1] >= 3.0
```

- [ ] **Step 5: Implement Page-style CUSUM**

```python
@dataclass(frozen=True, slots=True)
class CUSUMResult:
    scores: NDArray[np.float64]
    threshold: float
    first_alarm: int | None
    p0: float
    p1: float


def cusum_change_detection(observations, p0: float, p1: float, threshold: float) -> CUSUMResult:
    values = _binary_observations(observations)
    p0, p1 = _ordered_probabilities(p0, p1)
    threshold = _positive_finite(threshold, "threshold")
    increments = values * np.log(p1 / p0) + (1 - values) * np.log((1 - p1) / (1 - p0))
    scores = np.empty(values.size, dtype=float)
    running = 0.0
    for index, increment in enumerate(increments):
        running = max(0.0, running + float(increment))
        scores[index] = running
    alarms = np.flatnonzero(scores >= threshold)
    first = int(alarms[0] + 1) if alarms.size else None
    return CUSUMResult(scores, threshold, first, p0, p1)
```

- [ ] **Step 6: Run new and existing statistics tests**

Run: `.venv/bin/python -m pytest tests/test_sequential.py tests/test_statistics.py -q`

Expected: all tests pass with no warnings.

- [ ] **Step 7: Export the public API and commit**

```bash
git add src/roulette_lab/sequential.py src/roulette_lab/__init__.py tests/test_sequential.py
git commit -m "feat: add sequential evidence and change detection"
```

---

### Task 2: Posterior Decision and Tail-Risk Engine

**Files:**
- Create: `src/roulette_lab/decision.py`
- Create: `src/roulette_lab/risk.py`
- Create: `tests/test_decision.py`
- Create: `tests/test_risk.py`
- Modify: `src/roulette_lab/bankroll.py`
- Modify: `src/roulette_lab/__init__.py`

**Interfaces:**
- Consumes: hit count, trial count, Beta prior, net odds, credible level, lower quantile, future sample size, and simulated terminal bankrolls.
- Produces: `PosteriorEdgeSummary`, `posterior_edge_summary(...)`, `conditional_value_at_risk(...)`, and `build_risk_frontier(...) -> pd.DataFrame`.

- [ ] **Step 1: Write posterior edge tests around break-even**

```python
def test_posterior_edge_summary_matches_beta_distribution():
    result = posterior_edge_summary(
        hits=6, trials=100, prior_alpha=1.0, prior_beta=36.0,
        net_odds=35.0, level=0.95, lower_quantile=0.10, future_trials=100,
    )
    assert result.break_even_probability == pytest.approx(1 / 36)
    assert result.posterior_mean == pytest.approx(7 / 137)
    assert result.probability_positive_edge == pytest.approx(
        scipy.stats.beta.sf(1 / 36, 7, 130)
    )
    assert result.plugin_kelly > 0
    assert 0 <= result.quantile_kelly <= result.plugin_kelly


def test_fair_prior_with_no_data_allocates_no_robust_stake():
    result = posterior_edge_summary(0, 0, 1.0, 36.0, 35.0, 0.95, 0.10, 100)
    assert result.quantile_kelly == 0.0
```

- [ ] **Step 2: Run posterior tests and verify RED**

Run: `.venv/bin/python -m pytest tests/test_decision.py -q`

Expected: collection fails because `roulette_lab.decision` does not exist.

- [ ] **Step 3: Implement posterior decision summaries**

```python
@dataclass(frozen=True, slots=True)
class PosteriorEdgeSummary:
    posterior_alpha: float
    posterior_beta: float
    posterior_mean: float
    credible_interval: tuple[float, float]
    break_even_probability: float
    probability_positive_edge: float
    expected_net_return: float
    plugin_kelly: float
    quantile_probability: float
    quantile_kelly: float
    predictive_interval: tuple[int, int]


def posterior_edge_summary(hits, trials, prior_alpha, prior_beta, net_odds,
                           level, lower_quantile, future_trials) -> PosteriorEdgeSummary:
    # Validate integer counts and open-unit probabilities before calling SciPy.
    post_a = prior_alpha + hits
    post_b = prior_beta + trials - hits
    mean = post_a / (post_a + post_b)
    interval = scipy.stats.beta.interval(level, post_a, post_b)
    break_even = 1.0 / (net_odds + 1.0)
    edge_probability = scipy.stats.beta.sf(break_even, post_a, post_b)
    conservative_p = scipy.stats.beta.ppf(lower_quantile, post_a, post_b)
    predictive = scipy.stats.betabinom.interval(level, future_trials, post_a, post_b)
    return PosteriorEdgeSummary(
        post_a, post_b, mean, tuple(map(float, interval)), break_even,
        float(edge_probability), mean * net_odds - (1 - mean),
        kelly_fraction(mean, net_odds), float(conservative_p),
        kelly_fraction(float(conservative_p), net_odds),
        (int(predictive[0]), int(predictive[1])),
    )
```

- [ ] **Step 4: Write CVaR and frontier tests with an explicit loss convention**

```python
def test_cvar_is_mean_of_worst_terminal_losses():
    losses = np.array([-20.0, 0.0, 10.0, 30.0, 50.0])
    assert conditional_value_at_risk(losses, tail_probability=0.40) == pytest.approx(40.0)


def test_risk_frontier_has_one_sorted_point_per_fraction():
    table = build_risk_frontier(base_config, wheel, bet, rule, fractions=[0.25, 0.5, 1.0], seed=7)
    assert list(table["kelly_fraction_multiplier"]) == [0.25, 0.5, 1.0]
    assert set(["expected_log_growth", "terminal_cvar_shortfall", "expected_maximum_drawdown"]) <= set(table)
```

- [ ] **Step 5: Implement CVaR and deterministic risk-frontier composition**

```python
def conditional_value_at_risk(losses: ArrayLike, tail_probability: float = 0.05) -> float:
    values = _finite_vector(losses, "losses")
    tail_probability = _open_unit(tail_probability, "tail_probability")
    count = max(1, int(np.ceil(values.size * tail_probability)))
    return float(np.mean(np.sort(values)[-count:]))
```

`build_risk_frontier(base_config, wheel, bet, rule, fractions, seed) -> pd.DataFrame` accepts the implemented Kelly multipliers `0.25`, `0.5`, and `1.0`, maps them to quarter, half, and full Kelly, and rejects other values. It uses common random numbers by resetting the identical `seed` for each strategy. Each row contains terminal mean, median, probability of loss, maximum drawdown, expected log growth, and CVaR of non-negative shortfall `max(initial_bankroll - terminal_equity, 0)`.

- [ ] **Step 6: Add terminal CVaR to `RiskSummary` and its tests**

Update `summarize_bankroll` to calculate terminal shortfalls as `np.maximum(initial_bankroll - terminal_equity, 0.0)`, then call `conditional_value_at_risk(shortfalls, 0.05)`. Add this exact assertion to the existing bounded simulation test:

```python
assert np.isfinite(summary.terminal_cvar_shortfall)
assert summary.terminal_cvar_shortfall >= 0.0
```

- [ ] **Step 7: Run decision, risk, bet, and bankroll tests**

Run: `.venv/bin/python -m pytest tests/test_decision.py tests/test_risk.py tests/test_bets.py tests/test_bankroll.py -q`

Expected: all tests pass.

- [ ] **Step 8: Export APIs and commit**

```bash
git add src/roulette_lab/decision.py src/roulette_lab/risk.py src/roulette_lab/bankroll.py src/roulette_lab/__init__.py tests/test_decision.py tests/test_risk.py tests/test_bankroll.py
git commit -m "feat: add posterior decisions and tail risk"
```

---

### Task 3: Immutable Live Experiment State

**Files:**
- Create: `src/roulette_lab/experiment.py`
- Create: `tests/test_experiment.py`
- Modify: `src/roulette_lab/__init__.py`

**Interfaces:**
- Consumes: wheel, bet, special rule, seed, starting bankroll, stake, and requested spin count.
- Produces: `ExperimentState`, `new_experiment(...)`, `advance_experiment(...)`, and `reset_experiment(...)`.

- [ ] **Step 1: Write deterministic spin, batch, bankroll, and reset tests**

```python
def test_single_spins_equal_one_batch_for_the_same_seed():
    state = new_experiment(seed=42, initial_bankroll=1000.0)
    singles = state
    for _ in range(10):
        singles = advance_experiment(singles, fair_wheel, straight_17, SpecialRule.STANDARD, 10.0, 1)
    batch = advance_experiment(state, fair_wheel, straight_17, SpecialRule.STANDARD, 10.0, 10)
    assert singles.history == batch.history
    assert singles.bankroll == batch.bankroll


def test_reset_restores_seed_and_empty_history():
    advanced = advance_experiment(new_experiment(7, 500.0), fair_wheel, bet, rule, 5.0, 4)
    assert reset_experiment(advanced) == new_experiment(7, 500.0)
```

- [ ] **Step 2: Run experiment tests and verify RED**

Run: `.venv/bin/python -m pytest tests/test_experiment.py -q`

Expected: collection fails because `roulette_lab.experiment` does not exist.

- [ ] **Step 3: Implement immutable state and deterministic prefix generation**

```python
@dataclass(frozen=True, slots=True)
class ExperimentState:
    seed: int
    initial_bankroll: float
    history: tuple[str, ...] = ()
    bankroll: float = 0.0


def new_experiment(seed: int, initial_bankroll: float) -> ExperimentState:
    if isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0:
        raise ValueError("seed must be a non-negative integer.")
    if isinstance(initial_bankroll, bool) or not np.isfinite(initial_bankroll) or initial_bankroll <= 0:
        raise ValueError("initial_bankroll must be a positive finite number.")
    return ExperimentState(seed=seed, initial_bankroll=initial_bankroll, bankroll=initial_bankroll)


def advance_experiment(state, wheel, bet, rule, stake, count) -> ExperimentState:
    if rule is not SpecialRule.STANDARD:
        raise ValueError("Live experiment settlement currently requires the standard rule.")
    if isinstance(count, bool) or not isinstance(count, Integral) or count < 1:
        raise ValueError("count must be a positive integer.")
    if isinstance(stake, bool) or not np.isfinite(stake) or stake <= 0:
        raise ValueError("stake must be a positive finite number.")
    rng = np.random.default_rng(state.seed)
    draws = rng.choice(
        np.asarray(wheel.labels, dtype=object),
        size=len(state.history) + int(count),
        p=wheel.probabilities,
    )
    appended = tuple(str(value) for value in draws[-int(count):])
    bankroll = state.bankroll
    for result in appended:
        wager = min(float(stake), bankroll)
        bankroll += wager * bet.net_odds if result in bet.covered_labels else -wager
    return replace(state, history=state.history + appended, bankroll=float(bankroll))
```

The function records spins even after bankroll reaches zero, using a zero wager for later observations. This keeps the statistical experiment running while making the bankroll state explicit. Bet-wheel compatibility is checked through the existing `house_edge` validator before drawing.

- [ ] **Step 4: Add count-table and indicator helpers**

Implement `ExperimentState.counts(wheel) -> NDArray[np.int64]` with `np.array([self.history.count(label) for label in wheel.labels], dtype=np.int64)`. Implement `ExperimentState.indicators(label) -> NDArray[np.int64]` by validating a non-empty string and returning `np.fromiter((value == label for value in self.history), dtype=np.int64)`. Tests assert wheel-label order and reject labels absent from the supplied wheel before calling `indicators`.

- [ ] **Step 5: Run experiment and wheel/bet tests**

Run: `.venv/bin/python -m pytest tests/test_experiment.py tests/test_wheels.py tests/test_bets.py -q`

Expected: all tests pass.

- [ ] **Step 6: Export the API and commit**

```bash
git add src/roulette_lab/experiment.py src/roulette_lab/__init__.py tests/test_experiment.py
git commit -m "feat: add reproducible live roulette experiments"
```

---

### Task 4: V2 Deterministic Analysis and Figures

**Files:**
- Modify: `src/roulette_lab/analysis.py`
- Modify: `src/roulette_lab/figures.py`
- Modify: `scripts/run_analysis.py`
- Modify: `scripts/verify_artifacts.py`
- Modify: `tests/test_analysis.py`
- Modify: `tests/test_io_and_power.py`
- Modify: `tests/test_verify_artifacts.py`
- Add generated: `outputs/tables/sequential_evidence.csv`
- Add generated: `outputs/tables/change_point_results.csv`
- Add generated: `outputs/tables/posterior_edge.csv`
- Add generated: `outputs/tables/risk_frontier.csv`
- Add generated: `outputs/figures/07_sequential_evidence.png`
- Add generated: `outputs/figures/08_change_point_cusum.png`
- Add generated: `outputs/figures/09_posterior_edge.png`
- Add generated: `outputs/figures/10_risk_frontier.png`

**Interfaces:**
- Consumes: Tasks 1 and 2 public functions plus existing wheel, fairness, random-walk, and bankroll engines.
- Produces: an expanded `AnalysisBundle` with eleven tables and ten publication figures.

- [ ] **Step 1: Write bundle-schema and deterministic-scenario tests**

```python
def test_v2_bundle_contains_advanced_research_tables():
    bundle = run_full_analysis(AnalysisConfig.fast_test())
    assert set(["spin", "e_value", "fixed_horizon_p_value"]) <= set(bundle.sequential_evidence)
    assert set(["scenario", "first_alarm", "detection_delay"]) <= set(bundle.change_point_results)
    assert set(["posterior_mean", "probability_positive_edge", "quantile_kelly"]) <= set(bundle.posterior_edge)
    assert set(["kelly_fraction_multiplier", "terminal_cvar_shortfall"]) <= set(bundle.risk_frontier)
```

- [ ] **Step 2: Run analysis tests and verify RED**

Run: `.venv/bin/python -m pytest tests/test_analysis.py -q`

Expected: attribute failures for the four new tables.

- [ ] **Step 3: Extend configuration and bundle types**

Add these fields to `AnalysisConfig`:

```python
sequential_alternative_probability: float = 0.06
change_spin: int = 500
cusum_threshold: float = 4.0
posterior_prior_alpha: float = 1.0
posterior_prior_beta: float = 36.0
posterior_future_trials: int = 100
posterior_lower_quantile: float = 0.10
risk_multipliers: tuple[float, ...] = (0.25, 0.5, 1.0)
```

`AnalysisConfig.fast_test()` keeps these values and reduces only Monte Carlo experiment and path counts, preserving every output schema.

- [ ] **Step 4: Compose the four new publication tables**

Use one 1,000-spin fair sequence for the sequential null illustration, one 1,000-spin sequence changing from `1/37` to `0.06` at spin 500 for CUSUM, the existing biased teaching sample for posterior decisions, and common-random-number simulations for the risk frontier. Include scenario labels, seeds, thresholds, path counts, and interpretation-safe metadata as columns.

- [ ] **Step 5: Write figure-presence and nonblank tests**

```python
def test_publication_figures_include_v2_outputs():
    figures = publication_figures(run_full_analysis(AnalysisConfig.fast_test()))
    assert set(figures) == {
        "01_wheel_layout", "02_house_edge_comparison", "03_lln_convergence",
        "04_bias_residuals", "05_detection_power", "06_bankroll_risk",
        "07_sequential_evidence", "08_change_point_cusum",
        "09_posterior_edge", "10_risk_frontier",
    }
```

- [ ] **Step 6: Implement four restrained publication figures**

Use Matplotlib with shared typography and no decorative gradients. Include an evidence threshold on Figure 7, true change and alarm markers on Figure 8, break-even probability on Figure 9, and labelled strategy fractions on Figure 10. Preserve Figure 3 as the required random-walk/LLN evidence.

- [ ] **Step 7: Expand the artifact verifier**

Require eleven named CSV tables, ten named PNG figures, V2 column schemas, finite values, valid probability bounds, the fair-wheel no-edge condition, and exact manual-baseline phrases in README and the deliverables checklist.

- [ ] **Step 8: Generate outputs and run pipeline tests**

Run:

```bash
.venv/bin/python scripts/run_analysis.py
.venv/bin/python -m pytest tests/test_analysis.py tests/test_io_and_power.py tests/test_verify_artifacts.py -q
```

Expected: generated outputs are deterministic and all targeted tests pass.

- [ ] **Step 9: Commit the research pipeline**

```bash
git add src/roulette_lab/analysis.py src/roulette_lab/figures.py scripts/run_analysis.py scripts/verify_artifacts.py tests outputs
git commit -m "feat: publish advanced roulette inference results"
```

---

### Task 5: Evidence Cockpit Dashboard and Live Wheel

**Files:**
- Create: `src/roulette_lab/roulette_component.py`
- Modify: `src/roulette_lab/dashboard.py`
- Modify: `app.py`
- Modify: `.streamlit/config.toml`
- Modify: `tests/test_dashboard.py`
- Create: `tests/test_roulette_component.py`

**Interfaces:**
- Consumes: `ExperimentState`, sequential evidence, CUSUM, posterior decision, risk-frontier, and existing fixed-horizon view models.
- Produces: five view models and `roulette_wheel_html(labels, colours, result, spin_nonce, reduced_motion) -> str`.

- [ ] **Step 1: Write roulette component contract tests**

```python
def test_component_contains_correct_european_order_and_result():
    html = roulette_wheel_html(EUROPEAN_ORDER, colours, result="17", spin_nonce=4, reduced_motion=False)
    assert "32,15,19,4,21,2,25,17" in html
    assert 'data-result="17"' in html
    assert "prefers-reduced-motion" in html
    assert "cubic-bezier" in html


def test_component_rejects_result_not_on_wheel():
    with pytest.raises(ValueError, match="result"):
        roulette_wheel_html(EUROPEAN_ORDER, colours, result="00", spin_nonce=1, reduced_motion=False)
```

- [ ] **Step 2: Run component tests and verify RED**

Run: `.venv/bin/python -m pytest tests/test_roulette_component.py -q`

Expected: collection fails because `roulette_lab.roulette_component` does not exist.

- [ ] **Step 3: Implement the result-driven wheel HTML**

Generate sectors from validated labels and colours, calculate a deterministic target rotation from the result index and nonce, and render outer track, rotor, labels, ball, pointer, and result state. The public function starts with this contract:

```python
def roulette_wheel_html(
    labels: Sequence[str],
    colours: Sequence[str],
    result: str | None,
    spin_nonce: int,
    reduced_motion: bool = False,
) -> str:
    validated = _validate_wheel_component_inputs(labels, colours, result, spin_nonce)
    target_index = 0 if result is None else validated.labels.index(result)
    target_degrees = 5 * 360 + target_index * (360 / len(validated.labels))
    return _render_component_markup(validated, target_degrees, reduced_motion)
```

`_render_component_markup` serialises validated values with `json.dumps`; it does not interpolate untrusted HTML. JavaScript performs animation only and never calls randomness. CSS uses fixed dimensions, separate wheel and ball easing, stable controls, and a reduced-motion branch.

- [ ] **Step 4: Write advanced dashboard view-model tests**

```python
def test_live_view_updates_all_evidence_from_history():
    inputs = DashboardInputs.fast_test()
    state = advance_experiment(new_experiment(inputs.seed, inputs.initial_bankroll), wheel, bet, rule, 10.0, 50)
    view = build_live_experiment_view(state, inputs)
    assert view.sample_size == 50
    assert len(view.running_frequency) == 50
    assert len(view.e_values) == 50
    assert 0 <= view.posterior.probability_positive_edge <= 1
```

- [ ] **Step 5: Extend dashboard inputs and view models**

Add pre-specified target probability, CUSUM threshold, posterior prior strength, credible level, conservative quantile, future spins, CVaR level, and live experiment controls. Keep validation in dataclasses. Add `LiveExperimentView`, `EvidenceView`, and `DecisionRiskView` without placing Streamlit calls in `dashboard.py`.

- [ ] **Step 6: Replace the four-tab page with five continuous workspaces**

Create the five workspaces explicitly:

```python
live_tab, evidence_tab, risk_tab, mechanics_tab, methods_tab = st.tabs(
    ["Live Experiment", "Evidence", "Decision Risk", "Wheel Mechanics", "Methods"]
)
```

Render each tab through a focused `_render_*` function. Use one dark experiment stage, one off-white analysis surface, border rules, stable metric rows, and a single crimson accent. Keep control labels above widgets and explanations beside the outputs they qualify.

- [ ] **Step 7: Add live and variable-responsive charts**

Use Plotly for running frequency with posterior band, e-value with threshold, CUSUM with alarm marker, posterior probability density with break-even line, risk frontier, and bankroll fan chart. Set `uirevision` for stable interaction, disable unnecessary modebar tools, and give each chart a fixed responsive height.

- [ ] **Step 8: Add polished interaction states**

Single spin, batch 10/50/100, download history, and reset update `st.session_state`. Expensive simulations run from a form submit and use `st.cache_data` keyed by validated inputs. Display concrete empty, invalid-file, no-alarm, no-edge, and simulation-progress states. Buttons use active feedback; no looping decorative animation remains after settlement.

- [ ] **Step 9: Run dashboard tests and start the app**

Run:

```bash
.venv/bin/python -m pytest tests/test_dashboard.py tests/test_roulette_component.py tests/test_experiment.py -q
.venv/bin/streamlit run app.py --server.port 8501
```

Expected: tests pass and the local app loads without Python exceptions.

- [ ] **Step 10: Commit the dashboard**

```bash
git add app.py .streamlit/config.toml src/roulette_lab/dashboard.py src/roulette_lab/roulette_component.py tests/test_dashboard.py tests/test_roulette_component.py
git commit -m "feat: build the evidence cockpit dashboard"
```

---

### Task 6: Notebook, Report, Blog, and Application Narrative

**Files:**
- Modify: `scripts/build_notebook.py`
- Modify: `notebooks/roulette_analytics.ipynb`
- Modify: `report/technical_report.md`
- Modify: `scripts/build_report_pdf.py`
- Modify: `report/technical_report.pdf`
- Modify: `docs/technical_blog.md`
- Modify: `docs/methodology_map.md`
- Modify: `docs/ai_workflow.md`
- Modify: `docs/application_materials.md`
- Modify: `README.md`
- Modify: `tests/test_notebook.py`
- Modify: `tests/test_publication.py`

**Interfaces:**
- Consumes: generated V2 CSV tables and PNG figures from Task 4.
- Produces: one executed notebook, one 4,500 to 5,000 word report, a 13 to 16 page PDF, a focused technical blog, and admissions-ready repository copy.

- [ ] **Step 1: Tighten publication tests before rewriting**

```python
def test_report_prose_word_count_is_in_v2_range():
    assert 4_500 <= count_report_prose(ROOT / "report/technical_report.md") <= 5_000


def test_report_has_v2_research_sections_in_order():
    headings = [
        "Executive Summary", "Research Question and Provenance", "Probability Contract",
        "Fixed-Horizon Inference", "Sequential Evidence", "Change-Point Diagnostics",
        "Posterior Decisions", "Risk Frontier", "Software and Product Design",
        "Application Value", "Limitations", "Conclusion", "References",
    ]
    text = (ROOT / "report/technical_report.md").read_text(encoding="utf-8")
    assert [text.index(f"## {heading}") for heading in headings] == sorted(
        text.index(f"## {heading}") for heading in headings
    )
```

- [ ] **Step 2: Run publication tests and verify RED**

Run: `.venv/bin/python -m pytest tests/test_notebook.py tests/test_publication.py -q`

Expected: failures for word range, missing V2 headings, and missing notebook sections.

- [ ] **Step 3: Rebuild the notebook in the research argument order**

Generate and execute sections for exact wheel economics, random walk and LLN, fixed-horizon fairness, selection correction, sequential evidence, CUSUM, posterior edge uncertainty, robust Kelly, and CVaR frontier. Notebook cells import production functions and load generated CSV tables; they do not duplicate formulas in notebook-only code.

- [ ] **Step 4: Rewrite the technical report from generated evidence**

Use 4,500 to 5,000 English prose words. Replace repeated background with derivations, experimental design, numerical results, interpretation, and limits. Every new headline number must come from a named CSV table. Preserve a direct explanation of fair-wheel negative expectation, Random Walk, Kelly assumptions, post-selection bias, and responsible gambling.

- [ ] **Step 5: Redesign the PDF builder**

Use ReportLab with an A4 cover, restrained crimson rule, running section header, page numbers, consistent equation blocks, numbered tables and figures, and page-safe headings. Render 13 to 16 pages. Avoid Unicode mathematical subscripts and use ReportLab markup or plain ASCII notation.

- [ ] **Step 6: Rewrite supporting prose with the humanizer workflow**

Run the humanizer detector before and after editing `technical_report.md`, `technical_blog.md`, `README.md`, and `application_materials.md`. Use a professional technical voice, zero em dashes, no inflated claims, concrete numerical examples, varied sentence length, and explicit author judgement where appropriate.

- [ ] **Step 7: Update admissions and manual alignment**

README must contain project background, mathematical and technical methods, installation and usage, result screenshots, AI-use statement, live URL, limitations, and citation. Application materials must link the stronger research correction to Manchester mathematics, Programming with Python 70, product thinking, and the target postgraduate programmes without claiming that one project erases the transcript.

- [ ] **Step 8: Build and test publications**

Run:

```bash
.venv/bin/python scripts/build_notebook.py
.venv/bin/python scripts/build_report_pdf.py
.venv/bin/python -m pytest tests/test_notebook.py tests/test_publication.py -q
.venv/bin/python scripts/verify_artifacts.py
```

Expected: notebook executes, PDF builds, publication tests pass, and the verifier reports success.

- [ ] **Step 9: Commit publication outputs**

```bash
git add scripts/build_notebook.py scripts/build_report_pdf.py notebooks report docs README.md tests/test_notebook.py tests/test_publication.py
git commit -m "docs: publish the v2 research narrative"
```

---

### Task 7: Visual QA, Full Reproduction, Release, and Deployment

**Files:**
- Modify: `docs/assets/dashboard-desktop.png`
- Modify: `docs/assets/dashboard-mobile.png`
- Add: `docs/assets/live-experiment.png`
- Modify: `docs/visual_qa.md`
- Modify: `docs/deliverables_checklist.md`
- Modify: `deliverables/Roulette_Analytics_Lab_V1.zip`
- Modify: `deliverables/V1_MANIFEST.txt`

**Interfaces:**
- Consumes: the complete V2 repository.
- Produces: verified screenshots, a Project 1 requirement matrix, an exact-source ZIP, GitHub main update, and refreshed public Streamlit deployment.

- [ ] **Step 1: Run the full local reproducibility gate**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/run_analysis.py
.venv/bin/python scripts/build_notebook.py
.venv/bin/python scripts/build_report_pdf.py
.venv/bin/python scripts/verify_artifacts.py
git diff --exit-code
```

Expected: every command exits zero and deterministic rebuilds leave no uncommitted differences.

- [ ] **Step 2: Perform desktop browser QA at 1440x1000**

Check all five views, single spin, batch spin, reset, uploaded fair and biased CSVs, variable-responsive charts, no-edge Kelly state, CUSUM no-alarm and alarm states, downloads, and Methods content. Confirm the wheel is nonblank, settles on the Python result, and controls do not move during animation.

- [ ] **Step 3: Perform mobile browser QA at 390x844**

Check stacked live experiment layout, readable wheel labels, horizontal tab access, chart resizing, control text, metric containment, reduced-motion behavior, and absence of horizontal document overflow. Capture final PNG screenshots at exact viewport dimensions.

- [ ] **Step 4: Inspect PDF rendering**

Render every PDF page to PNG, inspect a contact sheet, and inspect dense equation, table, figure, and references pages at full resolution. Confirm 13 to 16 A4 pages, no clipped glyphs, no blank plots, no orphan headings, and stable page numbering.

- [ ] **Step 5: Complete the Project 1 manual matrix**

Update `docs/deliverables_checklist.md` so each manual requirement links to code, tests, output, report section, and dashboard evidence. Keep later portfolio projects explicitly out of scope. Record browser console results, viewport checks, interaction checks, and accepted limitations in `docs/visual_qa.md`.

- [ ] **Step 6: Commit the verified V2 source**

```bash
git add docs/assets docs/visual_qa.md docs/deliverables_checklist.md
git commit -m "test: verify the v2 portfolio experience"
```

- [ ] **Step 7: Build the exact-source release archive**

```bash
SOURCE_COMMIT=$(git rev-parse HEAD)
git archive --format=zip --output=/private/tmp/Roulette_Analytics_Lab_V2.zip "$SOURCE_COMMIT" -- . ':(exclude)deliverables'
unzip -t /private/tmp/Roulette_Analytics_Lab_V2.zip
shasum -a 256 /private/tmp/Roulette_Analytics_Lab_V2.zip
```

Copy the checked archive to `deliverables/Roulette_Analytics_Lab_V2.zip`. Update the external manifest with the exact source commit, archive SHA-256, date, excluded group PDF, and successful `unzip -t` result.

- [ ] **Step 8: Commit and push the release**

```bash
git add deliverables/Roulette_Analytics_Lab_V2.zip deliverables/V1_MANIFEST.txt
git commit -m "release: package roulette analytics lab v2"
git push origin codex/roulette-v1:main
```

- [ ] **Step 9: Verify GitHub Actions and public deployment**

Wait for the `Reproducibility` GitHub Actions run on the final commit and require a successful conclusion. Open `https://roulette-analytics-lab.streamlit.app/` in an anonymous session, verify HTTP 200, repeat the critical live spin and evidence checks, and confirm the repository README displays the V2 screenshots and link.

- [ ] **Step 10: Record final release evidence**

Run `git status --short --branch`, compare `HEAD` with `origin/main`, rerun `scripts/verify_artifacts.py`, and record the final commit, CI URL, live dashboard URL, ZIP path, and SHA-256 in the completion summary.
