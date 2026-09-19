# Task 7 Release Report

## Source QA

- Source baseline: `1c837c64a9a72912e56b7095b7f26fec2c31b53a` on `codex/roulette-v1`.
- Deterministic gate: `.venv/bin/python -m pytest -q`, `scripts/run_analysis.py`, `scripts/build_notebook.py`, `scripts/build_report_pdf.py`, `scripts/verify_artifacts.py`, and fallback-git `diff --exit-code` all passed. The suite reported 326 passed tests.
- Browser QA: `http://127.0.0.1:8501/`, desktop 1440x1000 and mobile 390x844. All five tabs, spin, Batch 10, reset, fair and biased imports, downloads, no-edge, no-alarm, CUSUM alarm, responsive layout, and Methods were checked. Console errors/warnings: 0/0.
- Wheel evidence: 37 labels, 1279x466 CSS pixels, nonblank screenshot pixels, deterministic settled result `8`, and no frame-relative control movement during animation.
- Screenshots: `docs/assets/dashboard-desktop.png`, `docs/assets/dashboard-mobile.png`, and `docs/assets/live-experiment.png`.
- PDF QA: 14 A4 pages rebuilt and rendered at 144 DPI; contact sheet plus full-resolution pages 4, 5, 10, and 14 inspected without clipped glyphs, blank plots, orphan headings, or broken page numbering.

## Pending External Release Evidence

This report will be updated after the V2 archive commit, GitHub Actions result, anonymous Streamlit HTTP/public-access check, and final `HEAD == origin/main` comparison. At this point no public deployment claim has been made.
