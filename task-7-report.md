# Task 7 Release Report

## Source QA

- Deterministic gate: `.venv/bin/python -m pytest -q`, `scripts/run_analysis.py`, `scripts/build_notebook.py`, `scripts/build_report_pdf.py`, `scripts/build_report_pdf_zh.py`, `scripts/verify_artifacts.py`, and fallback-git `diff --exit-code` all passed. The suite now reports 337 passed tests.
- Browser QA: `http://127.0.0.1:8501/`, desktop 1440x1000 and mobile 390x844. All five tabs, spin, Batch 10, reset, fair and biased imports, downloads, no-edge, no-alarm, CUSUM alarm, responsive layout, and Methods were checked. Console errors/warnings: 0/0.
- Wheel evidence: 37 labels, 1279x466 CSS pixels, nonblank screenshot pixels, deterministic settled result `8`, and no frame-relative control movement during animation.
- Screenshots: `docs/assets/dashboard-desktop.png`, `docs/assets/dashboard-mobile.png`, and `docs/assets/live-experiment.png`.
- PDF QA: the 13-page English report and 12-page Chinese report were rebuilt and rendered at 144 DPI. Both were inspected through full contact sheets and selected full-resolution pages without clipped glyphs, blank plots, orphan headings, missing Chinese glyphs, or broken page numbering. The application-value section is absent from both reports.

## Archive provenance

- The source commit, archive SHA-256, and `unzip -t` result, together with the creation date and exclusions, are recorded in the external `deliverables/V3_MANIFEST.txt` adjacent to the ZIP.
- Those values are post-source facts. This report is inside the source archive, so embedding them here would change the archive and checksum it describes; it cannot self-reference those facts truthfully.
- The V3 archive excludes `deliverables`, and the existing V1 and V2 archives remain preserved outside it. Push and CI run URLs are also post-source release evidence and are intentionally recorded outside the packaged report.

## Public deployment verification

- Canonical URL: [roulette-analytics-lab.streamlit.app](https://roulette-analytics-lab.streamlit.app/).
- Fresh anonymous-browser check: `curl -sSL --max-redirs 20 -c <fresh-jar> -b <fresh-jar> https://roulette-analytics-lab.streamlit.app/` began as a fresh zero-cookie session and reached HTTP 200 at the unchanged canonical URL after it retained only server-issued anonymous cookies across redirects.
- As observed during this check, the jar contained `streamlit_session`, `_streamlit_csrf`, and `proxy-tracking-id`. Cookie names may vary with Streamlit infrastructure changes. The earlier no-jar loop incorrectly discarded session cookies at every redirect, so it did not model a browser session.
- The in-app browser loaded the full five-tab V2 dashboard. The diagnostic replacement app and remote deployment branch remain an undocumented fallback; canonical documentation continues to use the original roulette URL.
