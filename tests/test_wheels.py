import numpy as np
import pytest

from roulette_lab.wheels import (
    WheelKind,
    make_biased_wheel,
    make_fair_wheel,
)


def test_fair_european_wheel_is_a_probability_space():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    assert len(wheel.labels) == 37
    assert wheel.labels[0] == "0"
    np.testing.assert_allclose(wheel.probabilities, np.full(37, 1 / 37))
    assert wheel.probabilities.sum() == pytest.approx(1.0)


def test_fair_american_wheel_labels_both_zero_pockets():
    wheel = make_fair_wheel(WheelKind.AMERICAN)

    assert len(wheel.labels) == 38
    assert wheel.labels[:2] == ("0", "00")
    np.testing.assert_allclose(wheel.probabilities, np.full(38, 1 / 38))
    assert wheel.colours[:2] == ("green", "green")


def test_wheel_labels_and_colours_are_tuples():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    assert isinstance(wheel.labels, tuple)
    assert isinstance(wheel.colours, tuple)


def test_wheel_probabilities_are_immutable():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    with pytest.raises(ValueError):
        wheel.probabilities[0] = 0.0


def test_biased_wheel_rejects_invalid_probabilities():
    with pytest.raises(ValueError, match="sum to one"):
        make_biased_wheel(WheelKind.EUROPEAN, np.full(37, 0.02))


def test_biased_wheel_preserves_valid_probability_vector():
    probabilities = np.full(37, 1 / 37)
    wheel = make_biased_wheel(WheelKind.EUROPEAN, probabilities)

    np.testing.assert_allclose(wheel.probabilities, probabilities)
    assert wheel.probabilities is not probabilities
