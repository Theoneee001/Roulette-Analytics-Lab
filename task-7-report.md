# Task 7 Release Report

## Source QA

- Source baseline: `1c837c64a9a72912e56b7095b7f26fec2c31b53a` on `codex/roulette-v1`.
- Final verified-public source commit: `a502289f52f27673f7174737da2db1bac459726b` (`docs: verify public Streamlit deployment`).
- Deterministic gate: `.venv/bin/python -m pytest -q`, `scripts/run_analysis.py`, `scripts/build_notebook.py`, `scripts/build_report_pdf.py`, `scripts/verify_artifacts.py`, and fallback-git `diff --exit-code` all passed. The suite reported 326 passed tests.
- Browser QA: `http://127.0.0.1:8501/`, desktop 1440x1000 and mobile 390x844. All five tabs, spin, Batch 10, reset, fair and biased imports, downloads, no-edge, no-alarm, CUSUM alarm, responsive layout, and Methods were checked. Console errors/warnings: 0/0.
- Wheel evidence: 37 labels, 1279x466 CSS pixels, nonblank screenshot pixels, deterministic settled result `8`, and no frame-relative control movement during animation.
- Screenshots: `docs/assets/dashboard-desktop.png`, `docs/assets/dashboard-mobile.png`, and `docs/assets/live-experiment.png`.
- PDF QA: 14 A4 pages rebuilt and rendered at 144 DPI; contact sheet plus full-resolution pages 4, 5, 10, and 14 inspected without clipped glyphs, blank plots, orphan headings, or broken page numbering.

## Release and deployment evidence

- QA source commit: `73732c9da68cc7dbea0989980728fc65a50ebcb3` (`test: verify the v2 portfolio experience`).
- V2 package release commit: `64794a5d270a0982f16c817af0f5508f46927a3c` (`release: package roulette analytics lab v2`).
- V2 archive: `deliverables/Roulette_Analytics_Lab_V2.zip`, rebuilt by fallback `git archive` from final source commit `a502289f52f27673f7174737da2db1bac459726b` with `deliverables` excluded. SHA-256: `d7bacd5b5c73ab34778f7abfd5f49e37ab714ac7d59b8a45225f87dc4afb26f8`. `unzip -t` completed with no errors. The existing V1 ZIP was preserved unchanged.
- Push target: [origin/main](https://github.com/Theoneee001/Roulette-Analytics-Lab/tree/main). GitHub Actions [Reproducibility run 35457461402](https://github.com/Theoneee001/Roulette-Analytics-Lab/actions/runs/35457461402) completed successfully for `64794a5d270a0982f16c817af0f5508f46927a3c`.
- Deployment: [roulette-analytics-lab.streamlit.app](https://roulette-analytics-lab.streamlit.app/) was woken and loaded the V2 dashboard in the available owner session. It showed `Make this app public` as checked, and the deployed single-spin control recorded one observation and settled the rotor on `8`.

## Public deployment verification

- Canonical URL: [roulette-analytics-lab.streamlit.app](https://roulette-analytics-lab.streamlit.app/).
- Fresh anonymous-browser check: `curl -sSL --max-redirs 20 -c <fresh-jar> -b <fresh-jar> https://roulette-analytics-lab.streamlit.app/` returned HTTP 200, kept the canonical final URL, and received a 9,782-byte Streamlit shell.
- The jar began empty and retained only server-issued anonymous `streamlit_session` and `_streamlit_csrf` cookies across redirects. The earlier no-jar loop incorrectly discarded those cookies at every redirect, so it did not model a browser session.
- The in-app browser loaded the full five-tab V2 dashboard. The diagnostic replacement app and remote deployment branch remain an undocumented fallback; canonical documentation continues to use the original roulette URL.
