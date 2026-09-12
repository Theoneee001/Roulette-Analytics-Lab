"""Generate deterministic example data and publication analysis artifacts."""

from pathlib import Path
import os
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))
os.environ.setdefault("MPLBACKEND", "Agg")
sys.path.insert(0, str(ROOT / "src"))

from roulette_lab.io import SpinDataset, write_spin_csv  # noqa: E402
from roulette_lab.analysis import AnalysisConfig, run_full_analysis  # noqa: E402
from roulette_lab.wheels import (  # noqa: E402
    WheelKind,
    WheelSpec,
    make_fair_wheel,
    wheel_with_single_pocket_probability,
)


EXAMPLE_SPINS = 1_000
UNBIASED_SEED = 2026091201
BIASED_SEED = 2026091202
BIASED_LABEL = "17"
BIASED_PROBABILITY = 0.06


def _simulate_dataset(wheel: WheelSpec, spins: int, seed: int) -> SpinDataset:
    rng = np.random.default_rng(seed)
    outcomes = tuple(rng.choice(wheel.labels, size=spins, p=wheel.probabilities))
    return SpinDataset(
        spin_indices=tuple(range(1, spins + 1)),
        spins=outcomes,
        wheel_kind=wheel.kind,
        wheel_labels=wheel.labels,
        wheel_probabilities=tuple(float(value) for value in wheel.probabilities),
    )


def main() -> None:
    data_directory = ROOT / "data"
    data_directory.mkdir(parents=True, exist_ok=True)
    fair_wheel = make_fair_wheel(WheelKind.EUROPEAN)
    biased_wheel = wheel_with_single_pocket_probability(
        fair_wheel, BIASED_LABEL, BIASED_PROBABILITY
    )
    write_spin_csv(
        _simulate_dataset(fair_wheel, EXAMPLE_SPINS, UNBIASED_SEED),
        data_directory / "example_unbiased_spins.csv",
    )
    write_spin_csv(
        _simulate_dataset(biased_wheel, EXAMPLE_SPINS, BIASED_SEED),
        data_directory / "example_biased_spins.csv",
    )
    run_full_analysis(AnalysisConfig()).write(ROOT / "outputs")


if __name__ == "__main__":
    main()
