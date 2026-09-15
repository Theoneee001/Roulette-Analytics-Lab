# Task 6 Publication Report

## Scope Completed

Task 6 now publishes the V2 research narrative: an executed notebook, a CSV-backed technical report and PDF, a technical blog, an expanded methodology map, AI-use documentation, admissions material, and a README that explains reproducibility and responsible use. Publication tests were tightened before the rewrite and observed failing before implementation.

## Counts and Layout

- Technical report prose: 4,944 words, measured by `count_report_prose` in `tests/test_publication.py`.
- Application personal-statement section: 152 words.
- PDF: 14 A4 pages, verified with `pdfinfo` after the final rebuild.
- PDF SHA-256 after final rebuild: `28d910558245b41513f65bcf0f6a4fa2a7b28f3e57948116a0355b758182aae1`.
- Headline values in the report are CSV markers resolved by `scripts/build_report_pdf.py`; named source tables include `house_edges.csv`, `bias_tests.csv`, `sequential_evidence.csv`, `change_point_results.csv`, `posterior_edge.csv`, and `risk_frontier.csv`.

## TDD and Build Evidence

- RED: the tightened notebook/publication suite first failed on the missing V2 notebook sections, missing production-interface references, outdated report headings, absent CSV evidence references, and the old 4,221-word report.
- Targeted final check: `tests/test_notebook.py`, `tests/test_publication.py`, and `tests/test_verify_artifacts.py` passed, 26 tests total.
- Full reproduction: `.venv/bin/python -m pytest -q` passed, 319 tests total.
- Rebuilt successfully: `scripts/run_analysis.py`, `scripts/build_notebook.py`, `scripts/build_report_pdf.py`, and `scripts/verify_artifacts.py`.
- Final artifact verifier result: `Artifact verification passed.`

## Humanizer Evidence

The requested Rust detector was attempted before prose editing and again after the final prose pass with `cargo build --release --quiet` in `/Users/jialianggong/.codex/skills/humanizer/scripts`. Both attempts failed during linking because the host points to a missing macOS Command Line Tools `xcrun` path. As a result, the detector produced no JSON metrics, so this report does not claim a burstiness or passive-voice score.

As a transparent fallback, the four required files were scanned before and after editing for em dashes and the configured plain-language watchlist. The final scan found zero em dashes in `report/technical_report.md`, `docs/technical_blog.md`, `README.md`, and `docs/application_materials.md`; it also found no matches for the scanned inflated-vocabulary terms. The prose was manually reviewed for unsupported certainty, fake claims, and admissions overstatement.

## Visual QA

The final PDF was rendered to 14 PNG pages with `pdftoppm` at 144 DPI. Pages 1, 2, 8, and 14 were inspected at full resolution: cover, headline table and dense opening text, sequential figure/change-point text, and conclusion/references. The review found no clipped glyphs, overlap, blank figure, or orphaned heading. `pdftoppm` emitted a non-fatal fontconfig warning but produced all 14 page images.

## Deviations

No publication requirement was intentionally omitted. The only environmental deviation is the unavailable Rust humanizer binary caused by the broken host Command Line Tools installation. The system `git` command has the same dependency issue; the bundled fallback Git binary was used for repository operations. The final commit hash is recorded after commit amendment.

## Commit

The Task 6 publication implementation commit is `ac0eeae8f1550d8a516d77dca76a6076f80dd456` with message `docs: publish the v2 research narrative`.

## Review Fixes, 15 September 2026

The Task 6 review findings were corrected in commit `54d7b9307e38596693aa195a1b2ca080975ac700`, `fix: address task 6 publication review`.

### Factual and Publication Corrections

- The Sequential Evidence section now states that `sequential_evidence.csv` contains only the generated `fair_null` path. The synthetic changed path, alarm, and reliability fields are attributed to `change_point_results.csv`.
- Table 1 now prints the exact CSV name, row filter, and column for each of its six metrics. The report distinguishes the 1.67% quarter-Kelly loss rate in `strategy_risk.csv` from the 2.07% rate in `risk_frontier.csv`: both use 3,000 paths, 300 spins, and the same constraints, but they are separate Monte Carlo samples with seeds 20261117 and 20261412. The frontier seed is shared across its three Kelly fractions, so the two tables are not directly paired.
- Report figures are numbered once in monotone order from Figure 1 through Figure 9. Each caption was checked against the plotted axes and series. The risk-frontier caption now describes expected log growth against Kelly fraction multiplier under common random outcomes.
- The Streamlit URL is labelled as a deployment target with public-access verification pending in Task 7. README, application material, the deliverables checklist, the visual QA record, publication tests, and the artifact verifier reject the former unverified public-live wording. The online demonstration remains a release checklist item.
- The report retains the required section order and admissions framing. The final count is 4,988 English prose words, and the personal-statement section remains 152 words.

### TDD and Verification Evidence

- RED publication run: seven new tests failed against the reviewed artifacts, covering the incorrect sequential scenario claim, missing Table 1 source fields, unexplained quarter-Kelly samples, duplicate figure numbers, overstated deployment status, split PDF paragraphs, and the forced conclusion page break.
- RED verifier run: `test_verifier_rejects_unverified_public_dashboard_wording` initially failed because the verifier accepted false live-public copy.
- Targeted final run: `.venv/bin/python -m pytest tests/test_notebook.py tests/test_publication.py tests/test_verify_artifacts.py -q` passed, 33 tests total.
- Full final run: `.venv/bin/python -m pytest -q` passed, 326 tests total.
- Fresh builds: `.venv/bin/python scripts/build_notebook.py` executed the production-importing notebook, and `.venv/bin/python scripts/build_report_pdf.py` rebuilt the report.
- Artifact gate: `.venv/bin/python scripts/verify_artifacts.py` reported `Artifact verification passed.` The verifier now checks the provisional deployment wording, PDF page range, and the presence of `Probability Contract` on page 4.

### PDF and Visual QA Evidence

The PDF builder now keeps each prose paragraph intact, reserves enough room after section headings, and has only the cover page break. The old forced break before Conclusion was removed. The final PDF is 14 A4 pages at 595.276 by 841.89 points, with SHA-256 `9245e425340bfe5ee24775fc72f45132d83f248551d43f86296f1cdd049514d5`.

All 14 pages were rendered at 144 DPI to 1191x1684 PNGs and inspected in four contact sheets. Pages 4 and 10 were also inspected at full resolution. Page 4 begins with `Probability Contract` and its opening paragraph; page 10 begins with the complete `Full plug-in Kelly` paragraph. No dropped first characters, clipping, overlap, broken glyphs, blank plots, or orphan headings were found. Page 13 is filled by Application Value and Limitations, while Conclusion and References share page 14. `pypdf` extraction confirmed every continuation page starts at a complete source paragraph or figure caption. Two consecutive final PDF builds produced the same hash. Poppler emitted a non-fatal fontconfig warning while rendering all pages successfully.

### Humanizer Evidence and Deviations

The Rust detector was attempted before the review edits and after the final prose pass. Both `cargo build --release --quiet` attempts exited 101 because `/Library/Developer/CommandLineTools/usr/bin/xcrun` is missing, so no detector JSON or burstiness metric was produced. This report does not substitute invented scores. An intermediate fallback scan found four blacklist hits in `technical_report.md` and one in `technical_blog.md`. After the final edit, `technical_report.md`, `technical_blog.md`, `README.md`, and `application_materials.md` each had zero em dashes and zero matches from the humanizer vocabulary blacklist.

No publication requirement was omitted. Public deployment was deliberately not asserted because Task 7 anonymous-access verification remains pending. The only tooling deviations were the unavailable Rust linker and Poppler's harmless fontconfig warning. The project added `pypdf` to its declared and locked dependencies so PDF text and page assertions run reproducibly in tests and the artifact verifier.
