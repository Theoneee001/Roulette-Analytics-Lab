import numpy as np
import pytest

from roulette_lab.sequential import cusum_change_detection, likelihood_ratio_path


def test_sequential_public_api_is_exported_from_package():
    from roulette_lab import (
        CUSUMResult,
        SequentialEvidence,
        cusum_change_detection as exported_cusum_change_detection,
        likelihood_ratio_path as exported_likelihood_ratio_path,
    )

    assert CUSUMResult.__name__ == "CUSUMResult"
    assert SequentialEvidence.__name__ == "SequentialEvidence"
    assert exported_cusum_change_detection is cusum_change_detection
    assert exported_likelihood_ratio_path is likelihood_ratio_path


def test_all_hits_have_exact_log_likelihood_path():
    result = likelihood_ratio_path([1, 1, 1], p0=1 / 37, p1=0.06, alpha=0.05)
    expected = np.arange(1, 4) * np.log(0.06 / (1 / 37))

    np.testing.assert_allclose(result.log_likelihood_ratio, expected)
    np.testing.assert_allclose(result.e_values, np.exp(expected))
    assert result.threshold == pytest.approx(20.0)
    assert result.first_crossing is None


@pytest.mark.parametrize("p0,p1", [(0, 0.1), (1, 0.9), (0.1, 0.1), (0.2, 0.1)])
def test_likelihood_ratio_rejects_invalid_probability_order(p0, p1):
    with pytest.raises(ValueError):
        likelihood_ratio_path([0, 1], p0=p0, p1=p1, alpha=0.05)


def test_likelihood_ratio_reports_one_indexed_first_threshold_crossing():
    result = likelihood_ratio_path([1, 1, 1], p0=1 / 37, p1=0.06, alpha=0.5)

    assert result.first_crossing == 1


@pytest.mark.parametrize(
    "observations",
    [[], [0, 2], [0.5, 1.0], [[0, 1]], [0, "1"]],
)
def test_sequential_tools_reject_non_binary_or_empty_observations(observations):
    with pytest.raises(ValueError):
        likelihood_ratio_path(observations, p0=1 / 37, p1=0.06, alpha=0.05)
    with pytest.raises(ValueError):
        cusum_change_detection(observations, p0=1 / 37, p1=0.06, threshold=3.0)


def test_sequential_tools_accept_boolean_observations():
    result = likelihood_ratio_path(
        np.array([True, False], dtype=bool), p0=1 / 37, p1=0.06, alpha=0.05
    )

    assert result.log_likelihood_ratio.shape == (2,)


@pytest.mark.parametrize("alpha", [0, 1, -0.1, float("nan"), True])
def test_likelihood_ratio_rejects_invalid_alpha(alpha):
    with pytest.raises(ValueError):
        likelihood_ratio_path([0, 1], p0=1 / 37, p1=0.06, alpha=alpha)


def test_cusum_resets_negative_evidence_to_zero():
    result = cusum_change_detection([0, 0, 0], p0=1 / 37, p1=0.06, threshold=3.0)

    np.testing.assert_array_equal(result.scores, np.zeros(3))
    assert result.first_alarm is None


def test_cusum_reports_first_threshold_crossing():
    result = cusum_change_detection([1] * 20, p0=1 / 37, p1=0.06, threshold=3.0)
    expected = int(np.ceil(3.0 / np.log(0.06 / (1 / 37))))

    assert result.first_alarm == expected
    assert result.scores[expected - 1] >= 3.0


@pytest.mark.parametrize("threshold", [0, -1, float("nan"), float("inf"), True])
def test_cusum_rejects_non_positive_or_non_finite_threshold(threshold):
    with pytest.raises(ValueError):
        cusum_change_detection([0, 1], p0=1 / 37, p1=0.06, threshold=threshold)
