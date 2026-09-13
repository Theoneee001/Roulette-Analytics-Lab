# Visual QA Record

## Dashboard desktop check

The final desktop review used a 1440x1000 viewport against the local Streamlit app on 13 September 2026. The four tabs were opened in sequence:

- **Wheel & Bets:** the European straight-bet view showed a 2.70% standard house edge, expected return `-0.0270`, 35:1 payout, and a nonblank pocket-probability chart.
- **Fairness Lab:** the built-in biased and unbiased states rendered, then both repository CSV files were uploaded through the visible file control. The unbiased upload selected pocket 32 and the biased upload selected pocket 17. Corrected and naive p-values changed with the source.
- **Bankroll Simulator:** the estimated win probability was changed from `0.02703` to `0.06000`. The strategy was changed from flat to quarter Kelly, and the terminal metrics plus path chart refreshed.
- **Methods & Limits:** expectation, maximum-count selection correction, Kelly's conditional assumptions, validation guidance, and the no-profit warning were all visible.

The saved desktop image is `docs/assets/dashboard-desktop.png`. It is a 1440x1000 PNG. No browser console errors were present. One `WebSocket onclose` warning was recorded during a deliberate page reload; the app reconnected and rendered normally.

## Dashboard mobile check

The responsive review used a 390x844 device viewport. An initial capture exposed clipped title and notice text, so the mobile CSS was revised to allow normal white-space, `overflow-wrap: anywhere`, smaller metric type, wrapping horizontal metric blocks, and a horizontally scrollable tab list. The final DOM measurements reported a 390-pixel viewport and 390-pixel document width. The title, supporting copy, metrics, scenario notice, and chart stay within the 358-pixel content column.

The final screenshot was captured through Chrome's device emulation after the built-in screenshot transport produced incorrect clipping metadata. It was inspected at original resolution and saved as `docs/assets/dashboard-mobile.png`, a true 390x844 PNG. The fourth tab remains available through the standard horizontal tab scroll on narrow screens; content does not overlap.

## Online deployment check

The production app was deployed from `main/app.py` on Streamlit Community Cloud with Python 3.12 and is available at [roulette-analytics-lab.streamlit.app](https://roulette-analytics-lab.streamlit.app/). Streamlit's sharing settings identify the app as public and searchable. A separate anonymous HTTP session completed the platform's session handshake and returned status 200.

The online review repeated the critical workflows at 1440x1000 and 390x844. All four tabs rendered. The biased repository CSV uploaded successfully and selected pocket 17 as the hottest pocket. Changing the bankroll strategy to quarter Kelly and raising the estimated win probability to `0.06000` recomputed terminal wealth, loss probability, and drawdown. The Methods & Limits tab retained the expected-value formula, selection-aware testing explanation, Kelly caveat, and responsible-use warning. Browser logs contained no errors or warnings after the completed checks.

## PDF check

`report/technical_report.pdf` was rendered to a contact sheet and inspected across all 11 pages. Pages 1, 7, 10, and 11 were also checked at higher resolution because they contain the metric panel, dense figures, a section boundary, and references. The review found:

- A4 page size with consistent page numbers and footer rules;
- readable equations, captions, labels, tables, and six nonblank figures;
- no cropped text, broken glyphs, blank plots, orphan headings, or incoherent overlaps;
- a clean page break before Conclusion, keeping the final argument and References together;
- stable output: two consecutive PDF builds produced the same SHA-256 hash.

## Accepted limitations

Streamlit's tab strip scrolls horizontally on a phone because four descriptive labels cannot remain readable in 390 pixels. This is an intentional native interaction, not hidden overflow. Owners see Streamlit's management control over the lower corner of the app; ordinary viewers do not receive that owner-only overlay.
