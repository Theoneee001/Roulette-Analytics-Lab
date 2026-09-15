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

## Online deployment status

The configured Streamlit target is [roulette-analytics-lab.streamlit.app](https://roulette-analytics-lab.streamlit.app/). The current endpoint presents an authentication boundary, so prior owner-session checks do not establish anonymous availability. Public access is pending public-access verification in Task 7. Until that release check runs, repository copy treats the URL as a deployment target rather than a public live demonstration.

## PDF check

`report/technical_report.pdf` has 14 pages. Each page was rendered to PNG at 144 DPI and inspected in four contact sheets. Pages 4 and 10 were also checked at the original 1191x1684 render size because the previous PDF had dropped the first character of text at those boundaries. The final SHA-256 is `9245e425340bfe5ee24775fc72f45132d83f248551d43f86296f1cdd049514d5`. The review found:

- A4 page size with consistent page numbers and footer rules;
- readable equations, captions, labels, the six-row source table, and nine nonblank report figures;
- unique figure numbering in order from Figure 1 through Figure 9;
- `Probability Contract` at the start of page 4 with its first paragraph, not stranded on page 3;
- complete opening text on pages 4 and 10, with no dropped characters, cropped text, broken glyphs, orphan headings, or overlaps;
- a well-filled page 13 containing Application Value and Limitations, followed by Conclusion and References on page 14;
- text extraction from all pages with every continuation starting at a complete source paragraph or figure caption.

## Accepted limitations

Streamlit's tab strip scrolls horizontally on a phone because four descriptive labels cannot remain readable in 390 pixels. This is an intentional native interaction, not hidden overflow. Owner sessions can display Streamlit's management control over the lower corner; that control is not part of the application content assessed in the local screenshots.
