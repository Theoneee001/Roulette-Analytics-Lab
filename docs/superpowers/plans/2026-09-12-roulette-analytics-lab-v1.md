# Roulette Analytics Lab V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible Python and Streamlit portfolio project that reconstructs the Group 40 roulette study, corrects its statistical errors, and satisfies every Roulette Project 1 requirement in the execution manual.

**Architecture:** All mathematics and simulation live in a Streamlit-independent package under `src/roulette_lab`. The command-line analysis, notebook, dashboard, figures, and report call the same tested interfaces so published outputs cannot drift. Deterministic builders generate versioned artifacts, while a permanent verifier checks mathematical identities, document requirements, and reproducibility.

**Tech Stack:** Python 3.12, NumPy, pandas, SciPy, Plotly, Matplotlib, Streamlit, nbformat/nbclient, ReportLab, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-12-roulette-analytics-lab-design.md`

## Global Constraints

- Describe the code as an independent Python reimplementation from the paper's mathematical specification; never claim a line-by-line MATLAB migration.
- Credit all five original group authors and distinguish the original paper from Jialiang's individual extension.
- Do not commit the group PDF without co-author permission; publish only its bibliographic record and SHA-256 checksum.
- Use explicit `numpy.random.Generator` objects and recorded integer seeds for every stochastic computation.
- Treat Kelly as conditional log-growth optimisation, not guaranteed profit; return zero allocation when the estimated edge is non-positive.
- Do not use the same observations to select a hot pocket and claim an unadjusted one-pocket p-value without a warning.
- Keep domain logic independent from Streamlit, Notebook, and PDF-generation code.
- The English technical report must contain 3,000-5,000 prose words under the repository's documented counting rule.
- Public prose must preserve numerical results, terminology, limitations, provenance, and a truthful AI-use statement.
- Dashboard charts must remain interpretable without relying only on red versus green.
- V1 is local and GitHub-ready; public Streamlit deployment occurs after user acceptance.

---

## File Responsibility Map

| Path | Responsibility |
|---|---|
| `src/roulette_lab/wheels.py` | Wheel labels, colours, probability vectors, and validation |
| `src/roulette_lab/bets.py` | Bet definitions, payouts, exact expectation, special rules, and Kelly fractions |
| `src/roulette_lab/statistics.py` | Fairness tests, max-count correction, posterior estimates, and power studies |
| `src/roulette_lab/bankroll.py` | Stateful strategy simulation and path-level risk metrics |
| `src/roulette_lab/analysis.py` | End-to-end experiment configuration and tidy result tables |
| `src/roulette_lab/figures.py` | Plotly and Matplotlib figures from analysis tables |
| `src/roulette_lab/io.py` | CSV schema validation and deterministic artifact writing |
| `app.py` | Streamlit composition only; no duplicated domain formulas |
| `scripts/run_analysis.py` | Rebuild data tables and figures from a fixed configuration |
| `scripts/build_notebook.py` | Create and execute the narrative notebook deterministically |
| `scripts/build_report_pdf.py` | Render the Markdown report as an A4 PDF |
| `scripts/verify_artifacts.py` | Cross-check outputs, decisions, documents, and deterministic publication |
| `tests/` | Unit, regression, integration, and publication tests |

---

### Task 1: Repository Scaffold and Fair Wheel Model

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `requirements-lock.txt`
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `src/roulette_lab/__init__.py`
- Create: `src/roulette_lab/wheels.py`
- Create: `tests/conftest.py`
- Create: `tests/test_wheels.py`

**Interfaces:**
- Produces: `WheelKind`, `Pocket`, `WheelSpec`, `make_fair_wheel(kind)`, `make_biased_wheel(kind, probabilities)`, and `validate_probability_vector(probabilities, size)`.
- `WheelSpec.probabilities` is an immutable `numpy.ndarray`; `WheelSpec.labels` and `WheelSpec.colours` are tuples.

- [ ] **Step 1: Write failing wheel tests**

```python
def test_fair_european_wheel_is_a_probability_space():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    assert len(wheel.labels) == 37
    assert wheel.labels[0] == "0"
    np.testing.assert_allclose(wheel.probabilities, np.full(37, 1 / 37))
    assert wheel.probabilities.sum() == pytest.approx(1.0)


def test_biased_wheel_rejects_invalid_probabilities():
    with pytest.raises(ValueError, match="sum to one"):
        make_biased_wheel(WheelKind.EUROPEAN, np.full(37, 0.02))
```

- [ ] **Step 2: Run the wheel tests and confirm failure**

Run: `python -m pytest tests/test_wheels.py -v`  
Expected: FAIL during import because `roulette_lab.wheels` does not exist.

- [ ] **Step 3: Implement the wheel model**

```python
class WheelKind(str, Enum):
    EUROPEAN = "european"
    AMERICAN = "american"


@dataclass(frozen=True)
class WheelSpec:
    kind: WheelKind
    labels: tuple[str, ...]
    colours: tuple[str, ...]
    probabilities: np.ndarray


def validate_probability_vector(probabilities: ArrayLike, size: int) -> np.ndarray:
    values = np.asarray(probabilities, dtype=float)
    if values.shape != (size,):
        raise ValueError(f"Expected {size} pocket probabilities.")
    if np.any(~np.isfinite(values)) or np.any(values < 0):
        raise ValueError("Pocket probabilities must be finite and non-negative.")
    if not np.isclose(values.sum(), 1.0, atol=1e-12):
        raise ValueError("Pocket probabilities must sum to one.")
    values.setflags(write=False)
    return values
```

Use the standard roulette red-number set and label American zero pockets as `"0"` and `"00"`.

- [ ] **Step 4: Add packaging metadata, licensing, and pinned dependencies**

Use a `src` layout in `pyproject.toml`, require Python `>=3.12,<3.13`, and list direct dependencies in `requirements.txt`. Generate `requirements-lock.txt` from the resolved environment after installation rather than inventing transitive versions. `LICENSE` must state that the new Python source is MIT-licensed, authored narrative remains copyright Jialiang Gong, and the original group paper is not distributed or relicensed.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_wheels.py -v`  
Expected: PASS.  
Commit: `feat: add validated roulette wheel model`

---

### Task 2: Bet Catalogue, Exact Returns, and Special Rules

**Files:**
- Create: `src/roulette_lab/bets.py`
- Create: `tests/test_bets.py`
- Modify: `src/roulette_lab/__init__.py`

**Interfaces:**
- Consumes: `WheelSpec`, `WheelKind`.
- Produces: `BetKind`, `SpecialRule`, `BetSpec`, `make_standard_bet(kind, selection, wheel)`, `expected_net_return(wheel, bet, rule) -> float`, `house_edge(...) -> float`, and `kelly_fraction(probability, net_odds, fraction=1.0) -> float`.
- A `BetSpec` stores the covered labels and net payout multiple; callers do not pass an unrelated free-form payout.

- [ ] **Step 1: Write failing expectation tests**

```python
@pytest.mark.parametrize(
    ("wheel_kind", "expected_edge"),
    [(WheelKind.EUROPEAN, 1 / 37), (WheelKind.AMERICAN, 2 / 38)],
)
def test_straight_up_house_edge(wheel_kind, expected_edge):
    wheel = make_fair_wheel(wheel_kind)
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), wheel)
    assert house_edge(wheel, bet, SpecialRule.STANDARD) == pytest.approx(expected_edge)


def test_european_la_partage_halves_even_money_edge():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.RED, (), wheel)
    assert house_edge(wheel, bet, SpecialRule.LA_PARTAGE) == pytest.approx(1 / 74)


def test_kelly_requires_probability_above_break_even():
    assert kelly_fraction(1 / 37, 35) == 0.0
    assert kelly_fraction(1 / 36, 35) == pytest.approx(0.0)
    assert kelly_fraction(0.03, 35) > 0.0
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_bets.py -v`  
Expected: FAIL because bet interfaces are missing.

- [ ] **Step 3: Implement typed bets and exact expectation**

Use payout multiples `35, 17, 11, 8, 5, 2, 2, 1` for straight, split, street, corner, six-line, dozen, column, and even-money bets. Validate the selection size and labels for every bet.

```python
def expected_net_return(wheel: WheelSpec, bet: BetSpec, rule: SpecialRule) -> float:
    win_probability = sum(
        wheel.probabilities[wheel.labels.index(label)] for label in bet.covered_labels
    )
    zero_probability = sum(
        wheel.probabilities[wheel.labels.index(label)]
        for label in wheel.labels
        if label in {"0", "00"}
    )
    if rule is SpecialRule.LA_PARTAGE:
        return win_probability * bet.net_odds - (1 - win_probability - zero_probability) - 0.5 * zero_probability
    return win_probability * bet.net_odds - (1 - win_probability)
```

Reject La Partage and En Prison for non-European or non-even-money bets.

- [ ] **Step 4: Implement En Prison and Kelly controls**

Represent the prison state explicitly and solve its expected value recursively. For a fair European even-money bet, verify that the expectation is `-1/74` per initial stake. Clamp Kelly to `[0, 1]`, validate `net_odds > 0`, and multiply by `fraction` only after computing full Kelly.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_bets.py -v`  
Expected: PASS.  
Commit: `feat: add exact roulette bet economics`

---

### Task 3: Global Fairness and Selection-Aware Bias Tests

**Files:**
- Create: `src/roulette_lab/statistics.py`
- Create: `tests/test_statistics.py`
- Modify: `src/roulette_lab/__init__.py`

**Interfaces:**
- Consumes: `WheelSpec` and integer count arrays.
- Produces: `FairnessResult`, `MaxCountResult`, `PosteriorEstimate`, `chi_square_fairness(counts, wheel)`, `monte_carlo_global_pvalue(counts, wheel, simulations, rng)`, `max_count_test(counts, wheel, simulations, rng)`, `dirichlet_posterior(counts, prior_strength, level)`, and `split_spin_history(spins, validation_fraction, rng)`.

- [ ] **Step 1: Write failing statistical tests**

```python
def test_chi_square_matches_scipy():
    counts = np.array([12] * 36 + [13])
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    result = chi_square_fairness(counts, wheel)
    expected = scipy.stats.chisquare(counts, np.full(37, counts.sum() / 37))
    assert result.statistic == pytest.approx(expected.statistic)
    assert result.p_value == pytest.approx(expected.pvalue)
    assert result.degrees_of_freedom == 36


def test_small_expected_counts_require_monte_carlo():
    result = chi_square_fairness(np.bincount(np.arange(20) % 37, minlength=37), make_fair_wheel(WheelKind.EUROPEAN))
    assert result.asymptotic_valid is False
    assert "Monte Carlo" in result.warning


def test_max_count_test_is_reproducible():
    counts = np.array([25] + [10] * 36)
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    a = max_count_test(counts, wheel, 4_000, np.random.default_rng(71))
    b = max_count_test(counts, wheel, 4_000, np.random.default_rng(71))
    assert a == b
    assert a.familywise_p_value >= a.naive_p_value
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_statistics.py -v`  
Expected: FAIL because the statistics module is missing.

- [ ] **Step 3: Implement the global tests**

Calculate Pearson residuals and Cramer's `V` alongside the test result. The Monte Carlo p-value must use the add-one correction:

```python
p_value = (1 + np.count_nonzero(simulated_statistics >= observed_statistic)) / (simulations + 1)
```

The asymptotic result is valid only when every expected count is at least five.

- [ ] **Step 4: Implement post-selection correction and posterior estimates**

For the max-count test, simulate complete multinomial samples and compare each simulated maximum with the observed maximum. Also return:

```python
naive_p = scipy.stats.binom.sf(observed_max - 1, n, 1 / pocket_count)
bonferroni_p = min(1.0, pocket_count * naive_p)
```

For each pocket, use a symmetric Dirichlet prior. Report posterior mean and a marginal Beta credible interval. `split_spin_history` must create disjoint estimation and validation samples.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_statistics.py -v`  
Expected: PASS.  
Commit: `feat: add selection-aware wheel bias tests`

---

### Task 4: Detection Power and Reproducible Spin Data

**Files:**
- Create: `src/roulette_lab/io.py`
- Create: `data/README.md`
- Create: `tests/test_io_and_power.py`
- Modify: `src/roulette_lab/wheels.py`
- Modify: `src/roulette_lab/statistics.py`

**Interfaces:**
- Consumes: wheel definitions and CSV bytes or paths.
- Produces: `SpinDataset`, `read_spin_csv(source, wheel)`, `write_spin_csv(dataset, path)`, `wheel_with_single_pocket_probability(base_wheel, label, probability)`, `simulate_spin_counts(wheel, spins, rng)`, and `estimate_detection_power(null_wheel, alternative_wheel, spins, alpha, experiments, rng)`.

- [ ] **Step 1: Write failing data and power tests**

```python
def test_csv_reader_rejects_unknown_pockets(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("spin,pocket\n1,99\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown pocket"):
        read_spin_csv(path, make_fair_wheel(WheelKind.EUROPEAN))


def test_power_rises_for_a_stronger_bias():
    null = make_fair_wheel(WheelKind.EUROPEAN)
    weak = wheel_with_single_pocket_probability(null, "17", 0.04)
    strong = wheel_with_single_pocket_probability(null, "17", 0.07)
    weak_power = estimate_detection_power(null, weak, 1_000, 0.05, 1_000, np.random.default_rng(8))
    strong_power = estimate_detection_power(null, strong, 1_000, 0.05, 1_000, np.random.default_rng(8))
    assert strong_power.estimated_power > weak_power.estimated_power
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_io_and_power.py -v`  
Expected: FAIL because data interfaces are missing.

- [ ] **Step 3: Implement CSV validation and deterministic examples**

Require columns `spin` and `pocket`, unique consecutive positive spin indices, valid pocket labels, and no missing values. `wheel_with_single_pocket_probability` sets the named pocket to the requested probability and redistributes the remaining mass proportionally across all other pockets. Generate `data/example_unbiased_spins.csv` and `data/example_biased_spins.csv` from fixed seeds in `scripts/run_analysis.py`; do not hand-edit generated rows.

- [ ] **Step 4: Implement power estimation**

Use the same declared alpha and global chi-squared rule across experiments. Return estimated power, Monte Carlo standard error, sample size, experiment count, and seed metadata. Add a test that the fair-wheel false-positive estimate lies within a predeclared broad simulation tolerance around alpha.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_io_and_power.py -v`  
Expected: PASS.  
Commit: `feat: add validated spin data and power analysis`

---

### Task 5: Bankroll Strategies and Risk Metrics

**Files:**
- Create: `src/roulette_lab/bankroll.py`
- Create: `tests/test_bankroll.py`
- Modify: `src/roulette_lab/__init__.py`

**Interfaces:**
- Consumes: `WheelSpec`, `BetSpec`, `SpecialRule`, and an explicit RNG.
- Produces: `StrategyKind`, `BankrollConfig`, `BankrollSimulation`, `simulate_bankroll(config, wheel, bet, rule, rng)`, and `summarize_bankroll(simulation) -> RiskSummary`.
- `BankrollSimulation.paths` has shape `(path_count, spins + 1)` and includes the initial bankroll in column zero.
- `BankrollConfig.custom_net_odds` defaults to `None`. A positive value overrides the standard payout only in a visibly labelled hypothetical sensitivity run; exact casino house-edge tables always use the standard `BetSpec.net_odds`.

- [ ] **Step 1: Write failing strategy tests**

```python
def test_no_edge_kelly_places_no_bet():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), wheel)
    config = BankrollConfig(initial_bankroll=1_000, base_stake=10, spins=50, paths=20, strategy=StrategyKind.KELLY, estimated_win_probability=1 / 37)
    result = simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(4))
    np.testing.assert_allclose(result.paths, 1_000)


def test_stop_loss_freezes_a_path_after_threshold():
    wheel = wheel_with_single_pocket_probability(
        make_fair_wheel(WheelKind.EUROPEAN), "17", 0.0
    )
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), wheel)
    config = BankrollConfig(initial_bankroll=100, base_stake=20, spins=20, paths=1, strategy=StrategyKind.FLAT, stop_loss=60)
    result = simulate_bankroll(config, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(1))
    hit = np.flatnonzero(result.paths[0] <= 60)[0]
    assert np.unique(result.paths[0, hit:]).size == 1


def test_fixed_seed_reproduces_paths():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.RED, (), wheel)
    config = BankrollConfig(initial_bankroll=500, base_stake=5, spins=30, paths=10, strategy=StrategyKind.FLAT)
    rule = SpecialRule.STANDARD
    a = simulate_bankroll(config, wheel, bet, rule, np.random.default_rng(19))
    b = simulate_bankroll(config, wheel, bet, rule, np.random.default_rng(19))
    np.testing.assert_array_equal(a.paths, b.paths)


def test_custom_odds_are_explicit_and_change_only_simulated_payout():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    bet = make_standard_bet(BetKind.STRAIGHT, ("17",), wheel)
    standard = BankrollConfig(initial_bankroll=500, base_stake=5, spins=1, paths=10_000, strategy=StrategyKind.FLAT)
    custom = replace(standard, custom_net_odds=40)
    standard_result = simulate_bankroll(standard, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(12))
    custom_result = simulate_bankroll(custom, wheel, bet, SpecialRule.STANDARD, np.random.default_rng(12))
    assert custom_result.payout_label == "Custom hypothetical odds: 40:1"
    assert standard_result.paths[:, -1].max() == 675
    assert custom_result.paths[:, -1].max() == 700
    assert house_edge(wheel, bet, SpecialRule.STANDARD) == pytest.approx(1 / 37)
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_bankroll.py -v`  
Expected: FAIL because bankroll interfaces are missing.

- [ ] **Step 3: Implement strategy state transitions**

Loop over spins but update all active paths vectorially. Flat uses the base stake. Martingale doubles after a loss and resets after a win. Reverse Martingale doubles after a win and resets after a loss. Kelly recalculates from current bankroll using the configured full, half, or quarter multiplier. Enforce bankroll, table limit, minimum chip, stop-loss, and take-profit before every round.

- [ ] **Step 4: Implement risk summaries**

Return terminal mean, median, standard deviation, 5th and 95th percentiles, probability of loss, probability of ruin, expected maximum drawdown, and median maximum drawdown. Include the number of paths and spins. Add a test showing the analytical one-spin mean agrees with a large fixed-seed simulation within five Monte Carlo standard errors.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_bankroll.py -v`  
Expected: PASS.  
Commit: `feat: simulate roulette bankroll risk`

---

### Task 6: Analysis Pipeline, Tables, and Figures

**Files:**
- Create: `src/roulette_lab/analysis.py`
- Create: `src/roulette_lab/figures.py`
- Create: `scripts/run_analysis.py`
- Create: `tests/test_analysis.py`
- Create through script: `outputs/tables/*.csv`
- Create through script: `outputs/figures/*.png`
- Create through script: `outputs/analysis_summary.md`

**Interfaces:**
- Consumes: all domain modules.
- Produces: `AnalysisConfig`, `AnalysisBundle`, `run_full_analysis(config)`, and figure functions that accept tidy DataFrames and return Figure objects.
- Default seeds, simulation sizes, alpha, wheel scenarios, and strategy settings live in one immutable `AnalysisConfig`.

- [ ] **Step 1: Write failing pipeline tests**

```python
def test_default_analysis_contains_manual_evidence():
    bundle = run_full_analysis(AnalysisConfig.fast_test())
    assert {"european", "american", "la_partage", "en_prison"} <= set(bundle.house_edges["rule"])
    assert {"flat", "martingale", "reverse_martingale", "full_kelly", "half_kelly"} <= set(bundle.strategy_risk["strategy"])
    assert {"naive_p_value", "bonferroni_p_value", "familywise_p_value"} <= set(bundle.bias_tests.columns)


def test_default_analysis_is_reproducible():
    a = run_full_analysis(AnalysisConfig.fast_test())
    b = run_full_analysis(AnalysisConfig.fast_test())
    pd.testing.assert_frame_equal(a.strategy_risk, b.strategy_risk)
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_analysis.py -v`  
Expected: FAIL because the analysis module is missing.

- [ ] **Step 3: Implement the shared analysis bundle**

Generate tables for exact house edges, law-of-large-numbers convergence, global and max-count tests, detection power, Kelly sensitivity, and strategy risk. Use a small `fast_test()` configuration for tests and a larger publication configuration for tracked results.

- [ ] **Step 4: Implement publication figures**

Create at least six figures: wheel layout, house-edge comparison, law-of-large-numbers convergence, observed-versus-expected residuals, detection-power curves, and bankroll-risk comparison. Use colour plus shape/line-style encoding and stable dimensions. Save high-resolution PNG files with metadata stripped or fixed.

- [ ] **Step 5: Generate artifacts, test, and commit**

Run: `python scripts/run_analysis.py`  
Run: `python -m pytest tests/test_analysis.py -v`  
Expected: generated files are stable and tests PASS.  
Commit: `feat: publish reproducible roulette analysis`

---

### Task 7: Streamlit Analytical Workspace

**Files:**
- Create: `app.py`
- Create: `src/roulette_lab/dashboard.py`
- Create: `.streamlit/config.toml`
- Create: `tests/test_dashboard.py`

**Interfaces:**
- Consumes: domain functions and figure builders.
- Produces: `DashboardInputs`, `validate_dashboard_inputs(values)`, `build_wheel_view(inputs)`, `build_fairness_view(dataset, inputs)`, and `build_bankroll_view(inputs)`.
- `app.py` only renders widgets and outputs; testable transformation code stays in `dashboard.py`.

- [ ] **Step 1: Write failing dashboard-view tests**

```python
def test_dashboard_rejects_stop_loss_above_initial_bankroll():
    with pytest.raises(ValueError, match="below the initial bankroll"):
        validate_dashboard_inputs({"initial_bankroll": 500, "stop_loss": 600})


def test_fairness_view_exposes_selection_warning():
    view = build_fairness_view(selected_hot_number_dataset, DashboardInputs.fast_test())
    assert "selected after observing" in view.selection_warning.lower()
    assert view.familywise_p_value >= view.naive_p_value
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_dashboard.py -v`  
Expected: FAIL because dashboard interfaces are missing.

- [ ] **Step 3: Implement the four-view workspace**

Use Streamlit tabs named `Wheel & Bets`, `Fairness Lab`, `Bankroll Simulator`, and `Methods & Limits`. Use icons only where they improve scanning. Provide controls for wheel, rule, bet, bankroll, base stake, stop-loss, take-profit, path count, spin count, bias strength, significance level, and seed. The odds control must switch between `Casino standard` and `Custom hypothetical`; custom odds must be positive and every affected result must carry the custom-scenario label. Uploaded CSV data must pass `read_spin_csv` before analysis.

- [ ] **Step 4: Apply the visual system and complete states**

Use off-white, near-black, roulette green, result red, and restrained gold; avoid gradients, casino imagery, oversized hero text, and nested cards. Implement empty upload guidance, invalid file messages, computation progress, no-edge Kelly state, insufficient sample warning, and download buttons for tidy results.

- [ ] **Step 5: Run tests, start the app, and commit**

Run: `python -m pytest tests/test_dashboard.py -v`  
Run: `streamlit run app.py --server.port 8501`  
Expected: tests PASS and the app serves without import or console errors.  
Commit: `feat: add interactive roulette analytics dashboard`

---

### Task 8: Executable Notebook and Formula-to-Code Traceability

**Files:**
- Create: `scripts/build_notebook.py`
- Create through script: `notebooks/roulette_analytics.ipynb`
- Create: `docs/methodology_map.md`
- Create: `tests/test_notebook.py`

**Interfaces:**
- Consumes: `run_full_analysis`, domain interfaces, and generated tables.
- Produces: a deterministic executed notebook and a map with columns `Concept`, `Equation`, `Python interface`, `Test`, `Figure`, and `Interpretation`.

- [ ] **Step 1: Write failing notebook tests**

```python
def test_notebook_is_executed_and_contains_required_sections():
    notebook = nbformat.read("notebooks/roulette_analytics.ipynb", as_version=4)
    headings = "\n".join(cell.source for cell in notebook.cells if cell.cell_type == "markdown")
    for title in ["House Edge", "Law of Large Numbers", "Bias Detection", "Kelly Criterion", "Bankroll Risk", "Limitations"]:
        assert title in headings
    assert all(cell.get("execution_count") is not None for cell in notebook.cells if cell.cell_type == "code")
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_notebook.py -v`  
Expected: FAIL because the notebook is absent.

- [ ] **Step 3: Build the narrative notebook**

Construct cells with `nbformat`, execute with `nbclient`, fix the kernel name and Python-version display, clear volatile timing metadata, and write atomically. The notebook must import package functions rather than duplicate formulas.

- [ ] **Step 4: Write the methodology map**

Map every major equation and correction to an exact function, test, table, and figure. Include the original paper's incorrect claim, the corrected statement, and the evidence used to validate it without using accusatory language.

- [ ] **Step 5: Rebuild twice, compare hashes, and commit**

Run: `python scripts/build_notebook.py` twice.  
Run: `shasum -a 256 notebooks/roulette_analytics.ipynb` after each build.  
Expected: identical hashes and notebook tests PASS.  
Commit: `docs: add executable roulette analysis notebook`

---

### Task 9: Report, Blog, Provenance, and Application Materials

**Files:**
- Create: `report/technical_report.md`
- Create: `scripts/build_report_pdf.py`
- Create through script: `report/technical_report.pdf`
- Create: `docs/technical_blog.md`
- Create: `docs/provenance.md`
- Create: `docs/ai_workflow.md`
- Create: `docs/application_materials.md`
- Create: `docs/deliverables_checklist.md`
- Create: `README.md`
- Create: `tests/test_publication.py`

**Interfaces:**
- Consumes: generated tables, figures, spec, and methodology map.
- Produces: complete manual-facing documentation and a deterministic 3,000-5,000-word A4 report.

- [ ] **Step 1: Write failing publication tests**

```python
def test_report_prose_word_count_is_in_range():
    assert 3_000 <= count_report_prose(Path("report/technical_report.md")) <= 5_000


def test_personal_statement_material_is_in_range():
    text = extract_named_section(Path("docs/application_materials.md"), "Personal Statement Material")
    assert 150 <= count_words(text) <= 200


def test_readme_contains_manual_requirements():
    readme = Path("README.md").read_text(encoding="utf-8")
    for phrase in ["Kelly", "chi-squared", "random walk", "Streamlit", "Reproducibility", "AI use", "Group 40"]:
        assert phrase.lower() in readme.lower()
```

Define `count_report_prose` in the test file to ignore headings, Markdown table rows, image syntax, and fenced code while counting English words and numbers with `re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*|[0-9]+(?:\\.[0-9]+)?%?", text)`. Define `extract_named_section` with a heading-bounded regular expression and fail clearly if the section is absent.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_publication.py -v`  
Expected: FAIL because publication files are absent.

- [ ] **Step 3: Draft the report and technical blog from generated evidence**

Write the report in this order: executive summary, provenance, problem definition, mathematical model, implementation, unbiased-wheel results, bias detection and correction, strategy risk, product design, application value, limitations, conclusion, references. Load all headline numbers from generated CSV files in the PDF builder; do not hard-code conflicting results in title panels.

The blog must explain negative drift, post-selection bias, and probability uncertainty in plain professional English. It must not tell readers how to gamble for profit.

- [ ] **Step 4: Complete README and application materials**

README sections: project background, source and individual extension, mathematical methods, architecture, installation, commands, dashboard controls, published results, screenshots, limitations, reproducibility, AI use, responsible-gambling notice, licence, and citation.

Application materials must include CV bullets, 150-200-word PS material, two-minute interview answer, technical walkthrough, personal-contribution answer, and separate mappings to CityU DTT, PolyU KTM, and HKUST BDT.

- [ ] **Step 5: Build PDF, run Humanizer, test, and commit**

Run the Humanizer detector before and after editing `README.md`, `report/technical_report.md`, `docs/technical_blog.md`, and `docs/application_materials.md`. Require zero em dashes, zero replaceable AI-vocabulary hits, burstiness at least `0.35`, and no unsupported claim changes.

Run: `python scripts/build_report_pdf.py`  
Run: `python -m pytest tests/test_publication.py -v`  
Expected: PDF exists, publication tests PASS, and all required sections contain real content.  
Commit: `docs: publish roulette portfolio narrative`

---

### Task 10: Permanent Artifact Verification and CI

**Files:**
- Create: `scripts/verify_artifacts.py`
- Create: `tests/test_verify_artifacts.py`
- Create: `.github/workflows/reproducibility.yml`

**Interfaces:**
- Consumes: all source modules and tracked outputs.
- Produces: `VerificationError`, `verify_artifacts(root: Path) -> None`, and a zero-exit CLI only when mathematics, files, counts, report, notebook, and published results agree.

- [ ] **Step 1: Write failing verifier tests**

```python
def test_verifier_rejects_an_incorrect_house_edge(tmp_path):
    copied = copy_artifacts(tmp_path)
    replace_csv_value(copied / "outputs/tables/house_edges.csv", "european", "house_edge", 0.0)
    with pytest.raises(VerificationError, match="European house edge"):
        verify_artifacts(copied)


def test_verifier_rejects_missing_manual_evidence(tmp_path):
    copied = copy_artifacts(tmp_path)
    (copied / "docs/technical_blog.md").unlink()
    with pytest.raises(VerificationError, match="technical blog"):
        verify_artifacts(copied)
```

In the test module, implement `copy_artifacts` with `shutil.copytree(PROJECT_ROOT, destination, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"))`. Implement `replace_csv_value` with pandas: load the CSV, select the unique row whose `rule` column matches the supplied key, replace the named value, and write the CSV without an index.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m pytest tests/test_verify_artifacts.py -v`  
Expected: FAIL because verifier interfaces are missing.

- [ ] **Step 3: Implement cross-artifact checks**

Verify exact European, American, La Partage, and En Prison house edges; probability sums; analytical-versus-simulation tolerances; selection-adjusted p-value ordering; report and PS word counts; required files and sections; notebook execution; figure dimensions; no missing values; and agreement between README/report headline values and CSV outputs.

- [ ] **Step 4: Add deterministic GitHub Actions**

The workflow must check out the repository, set up Python 3.12, install `requirements-lock.txt`, run the full test suite, rebuild analysis, execute the notebook, build the PDF, run the verifier, and execute `git diff --exit-code` for deterministic text/data/notebook artifacts. Exclude only the binary PDF from byte-level diff if ReportLab output cannot be stable after metadata normalisation.

- [ ] **Step 5: Run the full local gate and commit**

Run: `python -m pytest -q`  
Run: `python scripts/run_analysis.py`  
Run: `python scripts/build_notebook.py`  
Run: `python scripts/build_report_pdf.py`  
Run: `python scripts/verify_artifacts.py`  
Run: `git diff --check`  
Expected: all commands exit zero.  
Commit: `ci: enforce roulette portfolio reproducibility`

---

### Task 11: Browser Visual QA, Screenshots, and V1 Package

**Files:**
- Create through browser capture: `docs/assets/dashboard-desktop.png`
- Create through browser capture: `docs/assets/dashboard-mobile.png`
- Create: `docs/visual_qa.md`
- Modify: `README.md`
- Modify: `docs/deliverables_checklist.md`

**Interfaces:**
- Consumes: running Streamlit app and generated PDF.
- Produces: verified screenshots, visual-QA record, and a clean Git archive for user review.

- [ ] **Step 1: Start the dashboard and inspect desktop state**

Run: `streamlit run app.py --server.port 8501`. Use Playwright at `1440x1000` to inspect every tab, change controls, upload both sample CSVs, and confirm charts update without console errors. Save the desktop screenshot only after the working state is verified.

- [ ] **Step 2: Inspect mobile state**

Use a `390x844` viewport. Confirm controls, tabs, labels, tables, and charts do not overlap or overflow. Reset the viewport after capture. Record exact checks and any accepted limitations in `docs/visual_qa.md`.

- [ ] **Step 3: Render and inspect every PDF page**

Render `report/technical_report.pdf` to PNG pages. Build a contact sheet, inspect all pages, then inspect equations, tables, and dense figure pages at original resolution. Reject clipping, blank plots, broken glyphs, orphan headings, unreadable captions, or inconsistent page numbers.

- [ ] **Step 4: Run the final manual-requirement audit**

For each row in `docs/deliverables_checklist.md`, link to concrete evidence. Require explicit entries for Python reimplementation, Kelly, chi-squared, random walk, adjustable bankroll/odds/stop-loss, real-time curves, technical blog, AI workflow, README, code, data, results, screenshots, and local launch instructions. Mark online deployment as the sole post-acceptance item rather than falsely claiming it is live.

- [ ] **Step 5: Create and verify the V1 review package**

Create the Git archive `deliverables/Roulette_Analytics_Lab_V1.zip`, excluding `.git`, virtual environments, caches, and the unapproved group PDF. After the archive is final, create the sidecar file `deliverables/V1_MANIFEST.txt` containing the exact source commit and archive SHA-256 checksum; do not place this self-referential manifest inside the ZIP. Run `unzip -t`, then run the full test and verifier gate once more after packaging.

Commit: `release: prepare roulette analytics lab v1`

---

## Final Acceptance Evidence

The final V1 handoff must report:

- exact Git commit and clean worktree status;
- unit-test count and zero failures;
- artifact-verifier success;
- analytical benchmarks and simulation tolerances;
- technical-report prose count and PDF page count;
- Humanizer results for four public documents;
- desktop and mobile visual-QA results;
- archive path, integrity-test result, and SHA-256 checksum;
- a manual requirement matrix with no missing Roulette Project 1 item;
- an explicit note that online Streamlit deployment follows user acceptance.
