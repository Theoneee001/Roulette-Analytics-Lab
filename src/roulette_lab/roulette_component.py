"""Deterministic HTML renderer for the physical roulette rotor.

``WheelSpec.labels`` intentionally follows statistical label order. Physical
rotor order is a separate concern, kept here so drawing never changes a model
or chooses an outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
import html
import json
from numbers import Integral
from typing import Sequence


EUROPEAN_ROTOR_ORDER = (
    "0", "32", "15", "19", "4", "21", "2", "25", "17", "34", "6", "27", "13",
    "36", "11", "30", "8", "23", "10", "5", "24", "16", "33", "1", "20", "14",
    "31", "9", "22", "18", "29", "7", "28", "12", "35", "3", "26",
)
AMERICAN_ROTOR_ORDER = (
    "0", "28", "9", "26", "30", "11", "7", "20", "32", "17", "5", "22", "34",
    "15", "3", "24", "36", "13", "1", "00", "27", "10", "25", "29", "12", "8",
    "19", "31", "18", "6", "21", "33", "16", "4", "23", "35", "14", "2",
)
# Short aliases retain the component contract vocabulary used in the Task 5 brief.
EUROPEAN_ORDER = EUROPEAN_ROTOR_ORDER
AMERICAN_ORDER = AMERICAN_ROTOR_ORDER

_RED_LABELS = frozenset(
    {"1", "3", "5", "7", "9", "12", "14", "16", "18", "19", "21", "23", "25", "27", "30", "32", "34", "36"}
)


@dataclass(frozen=True, slots=True)
class _WheelComponentInputs:
    labels: tuple[str, ...]
    colours: tuple[str, ...]
    result: str | None
    spin_nonce: int


def rotor_order_for_labels(statistical_labels: Sequence[str]) -> tuple[str, ...]:
    """Return the canonical physical order after checking label-set equality."""

    labels = tuple(statistical_labels)
    if set(labels) == set(EUROPEAN_ROTOR_ORDER) and len(labels) == len(EUROPEAN_ROTOR_ORDER):
        return EUROPEAN_ROTOR_ORDER
    if set(labels) == set(AMERICAN_ROTOR_ORDER) and len(labels) == len(AMERICAN_ROTOR_ORDER):
        return AMERICAN_ROTOR_ORDER
    raise ValueError("labels must have the same set as a canonical physical rotor order.")


def colours_for_rotor(labels: Sequence[str]) -> tuple[str, ...]:
    """Derive display colours for a validated physical rotor label order."""

    rotor = rotor_order_for_labels(labels)
    return tuple("green" if value in {"0", "00"} else "red" if value in _RED_LABELS else "black" for value in rotor)


def roulette_wheel_html(
    labels: Sequence[str],
    colours: Sequence[str],
    result: str | None,
    spin_nonce: int,
    reduced_motion: bool = False,
) -> str:
    """Return a self-contained, result-driven roulette visualisation.

    Python owns the settled result and target angle. The embedded JavaScript
    only applies that already-determined transform once.
    """

    validated = _validate_wheel_component_inputs(labels, colours, result, spin_nonce)
    target_index = 0 if result is None else validated.labels.index(result)
    sector = 360.0 / len(validated.labels)
    target_degrees = (5 + validated.spin_nonce % 3) * 360.0 - target_index * sector
    return _render_component_markup(validated, target_degrees, reduced_motion)


def _validate_wheel_component_inputs(
    labels: Sequence[str], colours: Sequence[str], result: str | None, spin_nonce: int
) -> _WheelComponentInputs:
    label_values = tuple(labels)
    colour_values = tuple(colours)
    rotor_order_for_labels(label_values)
    if label_values not in {EUROPEAN_ROTOR_ORDER, AMERICAN_ROTOR_ORDER}:
        raise ValueError("labels must use the canonical physical rotor order.")
    if len(colour_values) != len(label_values) or any(value not in {"red", "black", "green"} for value in colour_values):
        raise ValueError("colours must be red, black, or green and match labels in length.")
    if result is not None and (not isinstance(result, str) or result not in label_values):
        raise ValueError("result must be a label on the physical rotor.")
    if isinstance(spin_nonce, bool) or not isinstance(spin_nonce, Integral) or spin_nonce < 0:
        raise ValueError("spin_nonce must be a non-negative integer.")
    return _WheelComponentInputs(label_values, colour_values, result, int(spin_nonce))


def _render_component_markup(values: _WheelComponentInputs, target_degrees: float, reduced_motion: bool) -> str:
    sector = 360.0 / len(values.labels)
    physical_colours = colours_for_rotor(values.labels)
    segments = ", ".join(
        f"{_colour_hex(colour)} {index * sector:.5f}deg {(index + 1) * sector:.5f}deg"
        for index, colour in enumerate(physical_colours)
    )
    labels_markup = "".join(
        f'<span class="rl-pocket" style="--angle:{index * sector:.5f}deg">{html.escape(label)}</span>'
        for index, label in enumerate(values.labels)
    )
    result_text = "Awaiting spin" if values.result is None else f"Result {values.result}"
    payload = json.dumps({"target": target_degrees, "reduced": bool(reduced_motion)})
    order = ",".join(values.labels)
    return f'''<!doctype html>
<html><head><meta charset="utf-8"><style>
* {{ box-sizing:border-box; }}
body {{ margin:0; background:#171816; color:#f7f7f4; font-family:"Avenir Next",Avenir,"Segoe UI",sans-serif; }}
.rl-stage {{ display:grid; place-items:center; min-height:455px; padding:18px; background:#171816; }}
.rl-wheel-wrap {{ width:min(92vw,430px); aspect-ratio:1; position:relative; display:grid; place-items:center; }}
.rl-pointer {{ position:absolute; z-index:4; top:0; left:50%; width:0; height:0; transform:translateX(-50%); border-left:13px solid transparent; border-right:13px solid transparent; border-top:24px solid #d32842; filter:drop-shadow(0 2px 0 rgba(0,0,0,.4)); }}
.rl-ball-track {{ position:absolute; inset:6.5%; border:2px solid #d7d8d2; border-radius:50%; opacity:.84; }}
.rl-ball {{ position:absolute; z-index:3; width:13px; height:13px; border-radius:50%; background:#f7f7f4; box-shadow:0 1px 5px #000; top:8%; left:calc(50% - 6.5px); transform:rotate(var(--ball-target)) translateY(30px); transform-origin:6.5px 165px; }}
.rl-rotor {{ width:82%; aspect-ratio:1; position:relative; border-radius:50%; border:8px solid #a9aaa4; box-shadow:inset 0 0 0 7px #343530, inset 0 0 0 19px #10110f, 0 10px 28px rgba(0,0,0,.36); transform:rotate(var(--target)); background:conic-gradient(from -4.86486deg, {segments}); }}
.rl-rotor::after {{ content:""; position:absolute; inset:29%; border-radius:50%; background:radial-gradient(circle at 35% 30%, #62635b, #282924 57%, #151613 58%); border:5px solid #888983; }}
.rl-pocket {{ position:absolute; inset:0; display:grid; place-items:start center; padding-top:6%; transform:rotate(var(--angle)); color:#f7f7f4; font-size:clamp(8px,2.1vw,12px); font-weight:700; line-height:1; text-shadow:0 1px 1px #000; }}
.rl-readout {{ position:absolute; z-index:5; bottom:-10px; left:50%; transform:translateX(-50%); min-width:132px; padding:7px 10px; background:#f7f7f4; color:#171816; text-align:center; font-size:13px; font-weight:700; border-radius:3px; }}
.is-spinning .rl-rotor {{ transition:transform 2.4s cubic-bezier(.14,.82,.18,1); }}
.is-spinning .rl-ball {{ transition:transform 1.72s cubic-bezier(.1,.76,.22,1); }}
@media (prefers-reduced-motion: reduce) {{ .rl-rotor,.rl-ball {{ transition:none !important; }} }}
</style></head><body>
<div class="rl-stage" data-result="{html.escape(values.result or '', quote=True)}" data-order="{html.escape(order, quote=True)}"><div class="rl-wheel-wrap">
<div class="rl-pointer"></div><div class="rl-ball-track"></div><div class="rl-ball"></div>
<div class="rl-rotor">{labels_markup}</div><div class="rl-readout">{html.escape(result_text)}</div>
</div></div>
<script>
(() => {{ const root=document.querySelector('.rl-stage'); const config={payload}; root.style.setProperty('--target', config.target+'deg'); root.style.setProperty('--ball-target', (config.target * -0.54)+'deg'); if (!config.reduced && !matchMedia('(prefers-reduced-motion: reduce)').matches && root.dataset.result) {{ requestAnimationFrame(() => root.classList.add('is-spinning')); setTimeout(() => root.classList.remove('is-spinning'), 2450); }} }})();
</script></body></html>'''


def _colour_hex(colour: str) -> str:
    return {"red": "#b62438", "black": "#22231f", "green": "#176046"}[colour]
