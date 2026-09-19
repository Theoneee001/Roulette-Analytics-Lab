# Visual QA Record

## Local release check

The Task 7 review ran against the local Streamlit application at `http://127.0.0.1:8501/` on 20 September 2026. Browser console capture recorded zero errors and zero warnings. The release screenshots are exact viewport captures:

| Capture | Viewport | Pixel result | Evidence |
| --- | --- | --- | --- |
| Desktop dashboard | 1440x1000 | 1,439,903 non-white pixels | [dashboard-desktop.png](assets/dashboard-desktop.png) |
| Mobile dashboard | 390x844 | 329,159 non-white pixels | [dashboard-mobile.png](assets/dashboard-mobile.png) |
| Settled live experiment | 1440x1000 | 758,538 dark rotor pixels and 30,647 crimson pixels | [live-experiment.png](assets/live-experiment.png) |

## Desktop interaction check

All five tabs rendered and were opened: **Live Experiment**, **Evidence**, **Decision Risk**, **Wheel Mechanics**, and **Methods**. The review also exercised a deterministic single spin, Batch 10, reset, both CSV teaching datasets, history and probability-table downloads, the no-edge decision state, CUSUM no-alarm and alarm states, responsive chart rendering, and Methods content.

- The default seeded single spin settled on `8`, matching `advance_experiment(new_experiment(20260912, 1000.0), ...)`.
- The visual rotor was nonblank at 1279x466 CSS pixels, displayed all 37 European labels, and had removed its `is-spinning` class after settlement.
- The six live controls kept identical frame-relative bounds during rotor animation. Browser viewport scrolling changed after Streamlit rerendering, but the controls did not shift relative to the rotor frame.
- One initial miss produced the visible `No CUSUM alarm has crossed the declared threshold.` state. Importing `data/example_biased_spins.csv` displayed the CUSUM chart's `First alarm` marker. Both `example_unbiased_spins.csv` and `example_biased_spins.csv` displayed successful import states.
- Running the no-observation/one-miss decision path displayed `The posterior does not put more than half its mass above break-even. Kelly outputs are shown as zero-stake evidence.`
- Browser download events confirmed both `roulette_history.csv` and `wheel_probabilities.csv` controls.

## Mobile check

At exactly 390x844, `documentElement.clientWidth` and `scrollWidth` were both 390. The live layout stacked without document-level horizontal overflow; metric text remained contained; the wheel labels were visible; and the native `Scroll tabs right` control made the horizontally overflowing tab strip accessible, including the Methods tab. The live screenshot records the imported biased state so the high-information metric and chart layout are also represented at mobile width.

The browser environment did not request reduced motion (`matchMedia('(prefers-reduced-motion: reduce)').matches` was `false`). The component's reduced-motion implementation is covered by `tests/test_roulette_component.py`: its generated markup includes the `prefers-reduced-motion` media query, which removes rotor and ball transitions. This is an accepted environment limitation, not a claim that the browser preference was forced during this capture.

## PDF check

`report/technical_report.pdf` was rebuilt and rendered in full at 144 DPI. `pdfinfo` confirmed 14 unencrypted A4 pages. The report has 14 pages. A 14-page contact sheet and full-resolution pages 4 (dense probability equations), 5 (figures), 10 (posterior figure), and 14 (conclusion and references) were inspected. The review found no blank plots, clipped glyphs, orphan headings, unstable page numbering, or cropped references. Full rendered pages were 1191x1684 pixels.

## Online deployment status

The canonical [verified public deployment](https://roulette-analytics-lab.streamlit.app/) was checked as an anonymous browser: `curl -sSL --max-redirs 20 -c <fresh-jar> -b <fresh-jar> https://roulette-analytics-lab.streamlit.app/` returned HTTP 200, retained the canonical final URL, and received a 9,782-byte Streamlit shell. The fresh anonymous cookie jar preserves only server-issued `streamlit_session` and `_streamlit_csrf` cookies across redirects; discarding those cookies on each request is not an anonymous-browser model. The in-app browser also loaded the complete five-tab V2 application. The owner-facing Streamlit panel had already deployed V2 and displayed `Make this app public` as checked. No WebSocket warning or error was recorded during this Task 7 browser capture.

## Accepted limitations

The tab strip intentionally scrolls horizontally at narrow widths so descriptive tab names remain readable. The local browser did not expose a reduced-motion preference override, so reduced-motion behavior is evidenced by the checked component CSS and unit test rather than a forced-preference visual capture.
