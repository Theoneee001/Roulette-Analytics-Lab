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
