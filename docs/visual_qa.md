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

## PDF check

`report/technical_report.pdf` was rendered to a contact sheet and inspected across all 11 pages. Pages 1, 7, 10, and 11 were also checked at higher resolution because they contain the metric panel, dense figures, a section boundary, and references. The review found:

- A4 page size with consistent page numbers and footer rules;
- readable equations, captions, labels, tables, and six nonblank figures;
- no cropped text, broken glyphs, blank plots, orphan headings, or incoherent overlaps;
- a clean page break before Conclusion, keeping the final argument and References together;
- stable output: two consecutive PDF builds produced the same SHA-256 hash.

## Accepted limitations

Streamlit's tab strip scrolls horizontally on a phone because four descriptive labels cannot remain readable in 390 pixels. This is an intentional native interaction, not hidden overflow. The public release is local and GitHub-ready; online Streamlit deployment remains a post-acceptance action.

