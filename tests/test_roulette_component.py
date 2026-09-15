import pytest

from roulette_lab.roulette_component import EUROPEAN_ROTOR_ORDER, roulette_wheel_html
from roulette_lab.wheels import make_fair_wheel, WheelKind


def test_component_contains_correct_european_order_and_result():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    html = roulette_wheel_html(
        EUROPEAN_ROTOR_ORDER, wheel.colours, result="17", spin_nonce=4, reduced_motion=False
    )

    assert "32,15,19,4,21,2,25,17" in html
    assert 'data-result="17"' in html
    assert "prefers-reduced-motion" in html
    assert "cubic-bezier" in html


def test_component_rejects_result_not_on_wheel():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    with pytest.raises(ValueError, match="result"):
        roulette_wheel_html(
            EUROPEAN_ROTOR_ORDER, wheel.colours, result="00", spin_nonce=1, reduced_motion=False
        )


def test_component_rejects_noncanonical_physical_order_even_when_labels_match():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    with pytest.raises(ValueError, match="physical rotor order"):
        roulette_wheel_html(
            wheel.labels, wheel.colours, result="17", spin_nonce=1, reduced_motion=False
        )
