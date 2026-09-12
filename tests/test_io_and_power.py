import copy
import io
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import scipy.stats

from roulette_lab.io import SpinDataset, read_spin_csv, write_spin_csv
from roulette_lab.statistics import (
    PowerEstimate,
    estimate_detection_power,
    simulate_spin_counts,
)
from roulette_lab.wheels import (
    WheelKind,
    make_biased_wheel,
    make_fair_wheel,
    wheel_with_single_pocket_probability,
)


def test_csv_reader_rejects_unknown_pockets(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("spin,pocket\n1,99\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown pocket"):
        read_spin_csv(path, make_fair_wheel(WheelKind.EUROPEAN))


def test_csv_reader_preserves_zero_zero_from_bytes_and_round_trips(tmp_path):
    wheel = make_fair_wheel(WheelKind.AMERICAN)
    dataset = read_spin_csv(b"spin,pocket\n1,00\n2,17\n", wheel)
    target = tmp_path / "spins.csv"

    write_spin_csv(dataset, target)
    round_tripped = read_spin_csv(target, wheel)

    assert isinstance(dataset, SpinDataset)
    assert dataset.spin_indices == (1, 2)
    assert dataset.spins == ("00", "17")
    assert dataset.wheel_kind is WheelKind.AMERICAN
    assert dataset.wheel_labels == wheel.labels
    assert dataset.wheel_probabilities == tuple(wheel.probabilities)
    assert round_tripped == dataset


def test_csv_reader_accepts_text_and_binary_file_objects():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    text_dataset = read_spin_csv(io.StringIO("spin,pocket\n1,0\n"), wheel)
    binary_dataset = read_spin_csv(io.BytesIO(b"spin,pocket\n1,0\n"), wheel)

    assert text_dataset == binary_dataset


@pytest.mark.parametrize(
    "contents, message",
    [
        ("spin,pocket,source\n1,0,camera\n", "columns"),
        ("spin,pocket\n1,0,extra\n", "exactly"),
        ("spin,pocket\n1,\n", "Missing"),
        ("spin,pocket\n1,0\n1,1\n", "unique consecutive"),
        ("spin,pocket\n1,0\n3,1\n", "unique consecutive"),
        ("spin,pocket\n01,0\n", "positive integers"),
    ],
)
def test_csv_reader_rejects_schema_and_index_errors(tmp_path, contents, message):
    path = tmp_path / "invalid.csv"
    path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        read_spin_csv(path, make_fair_wheel(WheelKind.EUROPEAN))


def test_csv_reader_accepts_required_columns_in_either_order():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    dataset = read_spin_csv(b"pocket,spin\n0,1\n", wheel)

    assert dataset.spin_indices == (1,)
    assert dataset.spins == ("0",)


def test_csv_writer_requires_a_spin_dataset(tmp_path):
    with pytest.raises(TypeError, match="SpinDataset"):
        write_spin_csv(None, tmp_path / "spins.csv")


def test_single_pocket_probability_preserves_other_relative_probabilities():
    probabilities = np.full(37, 0.8 / 36)
    probabilities[17] = 0.2
    base = make_biased_wheel(WheelKind.EUROPEAN, probabilities)

    biased = wheel_with_single_pocket_probability(base, "17", 0.1)
    target_index = base.labels.index("17")
    other_indices = np.arange(len(base.labels)) != target_index

    assert biased.kind is base.kind
    assert biased.labels == base.labels
    assert biased.colours == base.colours
    assert biased.probabilities[target_index] == pytest.approx(0.1)
    np.testing.assert_allclose(
        biased.probabilities[other_indices] / base.probabilities[other_indices],
        np.full(36, 0.9 / 0.8),
    )


@pytest.mark.parametrize("label, probability", [("99", 0.1), ("17", 0.0), ("17", 1.0), ("17", float("nan"))])
def test_single_pocket_probability_validates_label_and_probability(label, probability):
    with pytest.raises(ValueError):
        wheel_with_single_pocket_probability(
            make_fair_wheel(WheelKind.EUROPEAN), label, probability
        )


def test_simulate_spin_counts_is_seeded_and_has_the_requested_total():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    first = simulate_spin_counts(wheel, 250, np.random.default_rng(12))
    second = simulate_spin_counts(wheel, 250, np.random.default_rng(12))

    np.testing.assert_array_equal(first, second)
    assert first.shape == (37,)
    assert int(first.sum()) == 250


@pytest.mark.parametrize("spins", [0, -1, 2.5, True])
def test_simulate_spin_counts_requires_positive_integer_spins(spins):
    with pytest.raises(ValueError, match="positive integer"):
        simulate_spin_counts(
            make_fair_wheel(WheelKind.EUROPEAN), spins, np.random.default_rng(3)
        )


def test_simulate_spin_counts_requires_a_generator():
    with pytest.raises(TypeError, match="Generator"):
        simulate_spin_counts(make_fair_wheel(WheelKind.EUROPEAN), 1, None)


def test_power_estimate_uses_the_global_pearson_decision_rule():
    null = make_fair_wheel(WheelKind.EUROPEAN)
    alternative = wheel_with_single_pocket_probability(null, "17", 0.06)
    spins = 300
    alpha = 0.05
    experiments = 101
    expected_rng = np.random.default_rng(44)
    samples = expected_rng.multinomial(spins, alternative.probabilities, size=experiments)
    expected_counts = spins * null.probabilities
    expected_statistics = ((samples - expected_counts) ** 2 / expected_counts).sum(axis=1)
    expected_rejections = np.count_nonzero(
        expected_statistics >= scipy.stats.chi2.isf(alpha, len(null.labels) - 1)
    )

    result = estimate_detection_power(
        null, alternative, spins, alpha, experiments, np.random.default_rng(44)
    )

    assert isinstance(result, PowerEstimate)
    assert result.estimated_power == expected_rejections / experiments
    assert result.monte_carlo_standard_error == pytest.approx(
        np.sqrt(result.estimated_power * (1 - result.estimated_power) / experiments)
    )
    assert result.spins == spins
    assert result.experiments == experiments
    assert result.power == result.estimated_power
    assert result.monte_carlo_se == result.monte_carlo_standard_error
    assert result.sample_size == spins
    assert result.experiment_count == experiments
    assert result.alpha == alpha
    assert "Pearson" in result.decision_rule
    assert result.rng_bit_generator == "PCG64"
    assert result.rng_state


def test_power_false_positive_rate_is_broadly_calibrated_at_alpha():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    result = estimate_detection_power(
        wheel, wheel, 1_000, 0.05, 2_000, np.random.default_rng(1234)
    )

    assert 0.025 <= result.estimated_power <= 0.075


def test_power_rises_for_a_stronger_bias():
    null = make_fair_wheel(WheelKind.EUROPEAN)
    weak = wheel_with_single_pocket_probability(null, "17", 0.04)
    strong = wheel_with_single_pocket_probability(null, "17", 0.07)

    weak_power = estimate_detection_power(
        null, weak, 1_000, 0.05, 1_000, np.random.default_rng(8)
    )
    strong_power = estimate_detection_power(
        null, strong, 1_000, 0.05, 1_000, np.random.default_rng(8)
    )

    assert strong_power.estimated_power > weak_power.estimated_power


def test_power_estimation_is_reproducible_and_does_not_touch_global_rng():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    alternative = wheel_with_single_pocket_probability(wheel, "17", 0.05)
    rng = np.random.default_rng(700)
    state_before = copy.deepcopy(np.random.get_state())

    first = estimate_detection_power(wheel, alternative, 500, 0.05, 100, rng)
    second = estimate_detection_power(
        wheel, alternative, 500, 0.05, 100, np.random.default_rng(700)
    )

    assert first == second
    state_after = np.random.get_state()
    assert state_after[0] == state_before[0]
    np.testing.assert_array_equal(state_after[1], state_before[1])
    assert state_after[2:] == state_before[2:]


def test_power_estimation_records_state_for_non_default_seeded_generators():
    wheel = make_fair_wheel(WheelKind.EUROPEAN)
    rng = np.random.Generator(np.random.MT19937(91))

    result = estimate_detection_power(wheel, wheel, 100, 0.05, 10, rng)

    assert result.rng_bit_generator == "MT19937"
    assert result.rng_state


@pytest.mark.parametrize(
    "spins, alpha, experiments",
    [(0, 0.05, 10), (10, 0.0, 10), (10, 1.0, 10), (10, 0.05, 0)],
)
def test_power_estimation_validates_inputs(spins, alpha, experiments):
    wheel = make_fair_wheel(WheelKind.EUROPEAN)

    with pytest.raises(ValueError):
        estimate_detection_power(
            wheel, wheel, spins, alpha, experiments, np.random.default_rng(1)
        )


def test_analysis_entry_point_generates_fixed_seed_example_csvs():
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "scripts/run_analysis.py"], cwd=root, check=True)
    fair_wheel = make_fair_wheel(WheelKind.EUROPEAN)
    biased_wheel = wheel_with_single_pocket_probability(fair_wheel, "17", 0.06)

    unbiased = read_spin_csv(root / "data/example_unbiased_spins.csv", fair_wheel)
    biased = read_spin_csv(root / "data/example_biased_spins.csv", biased_wheel)
    expected_unbiased = tuple(
        np.random.default_rng(2026091201).choice(
            fair_wheel.labels, size=1_000, p=fair_wheel.probabilities
        )
    )
    expected_biased = tuple(
        np.random.default_rng(2026091202).choice(
            biased_wheel.labels, size=1_000, p=biased_wheel.probabilities
        )
    )

    assert unbiased.spins == expected_unbiased
    assert biased.spins == expected_biased
