"""Strict, reproducible CSV input and output for roulette spin histories."""

import csv
import io
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import BinaryIO, TextIO

from .wheels import WheelKind, WheelSpec, make_fair_wheel, validate_probability_vector


@dataclass(frozen=True, slots=True)
class SpinDataset:
    """An immutable spin history with the wheel snapshot that generated it."""

    spin_indices: tuple[int, ...]
    spins: tuple[str, ...]
    wheel_kind: WheelKind
    wheel_labels: tuple[str, ...]
    wheel_probabilities: tuple[float, ...]

    def __post_init__(self) -> None:
        indices = tuple(self.spin_indices)
        spins = tuple(self.spins)
        wheel_kind = WheelKind(self.wheel_kind)
        labels = tuple(self.wheel_labels)
        probabilities = tuple(float(value) for value in self.wheel_probabilities)
        if not indices or len(indices) != len(spins):
            raise ValueError("SpinDataset requires matching non-empty spin indices and spins.")
        if indices != tuple(range(1, len(indices) + 1)):
            raise ValueError("SpinDataset spin indices must be consecutive positive integers.")
        if labels != make_fair_wheel(wheel_kind).labels:
            raise ValueError("SpinDataset wheel_labels must match canonical labels for wheel_kind.")
        if any(not isinstance(spin, str) or spin not in labels for spin in spins):
            raise ValueError("SpinDataset contains an unknown pocket.")
        validate_probability_vector(probabilities, len(labels))
        object.__setattr__(self, "spin_indices", indices)
        object.__setattr__(self, "spins", spins)
        object.__setattr__(self, "wheel_kind", wheel_kind)
        object.__setattr__(self, "wheel_labels", labels)
        object.__setattr__(self, "wheel_probabilities", probabilities)


def _read_source(source: str | PathLike[str] | bytes | bytearray | BinaryIO | TextIO) -> str:
    if isinstance(source, (str, PathLike)):
        return Path(source).read_text(encoding="utf-8-sig")
    if isinstance(source, (bytes, bytearray)):
        return bytes(source).decode("utf-8-sig")
    if not hasattr(source, "read"):
        raise TypeError("source must be a path, UTF-8 bytes, or a readable file object.")
    content = source.read()
    if isinstance(content, bytes):
        return content.decode("utf-8-sig")
    if isinstance(content, str):
        return content
    raise TypeError("Readable file objects must return text or bytes.")


def read_spin_csv(
    source: str | PathLike[str] | bytes | bytearray | BinaryIO | TextIO,
    wheel: WheelSpec,
) -> SpinDataset:
    """Read exactly ``spin,pocket`` rows and validate them against ``wheel``."""

    if not isinstance(wheel, WheelSpec):
        raise TypeError("wheel must be a WheelSpec.")
    rows = csv.reader(io.StringIO(_read_source(source), newline=""))
    try:
        header = next(rows)
    except StopIteration as error:
        raise ValueError("CSV must contain spin and pocket columns.") from error
    if len(header) != 2 or set(header) != {"spin", "pocket"}:
        raise ValueError("CSV columns must be exactly spin,pocket.")
    spin_column = header.index("spin")
    pocket_column = header.index("pocket")

    spin_indices: list[int] = []
    spins: list[str] = []
    for row_number, row in enumerate(rows, start=2):
        if len(row) != 2:
            raise ValueError(f"CSV row {row_number} must contain exactly two columns.")
        spin_text = row[spin_column]
        pocket = row[pocket_column]
        if not spin_text.strip() or not pocket.strip():
            raise ValueError(f"Missing value in CSV row {row_number}.")
        if not spin_text.isdecimal() or spin_text != str(int(spin_text)):
            raise ValueError("Spin indices must be positive integers.")
        spin_index = int(spin_text)
        if spin_index <= 0:
            raise ValueError("Spin indices must be positive integers.")
        if pocket not in wheel.labels:
            raise ValueError(f"Unknown pocket {pocket!r} in CSV row {row_number}.")
        spin_indices.append(spin_index)
        spins.append(pocket)

    if not spin_indices:
        raise ValueError("CSV must contain at least one spin.")
    if tuple(spin_indices) != tuple(range(1, len(spin_indices) + 1)):
        raise ValueError("Spin indices must be unique consecutive positive integers.")
    return SpinDataset(
        spin_indices=tuple(spin_indices),
        spins=tuple(spins),
        wheel_kind=wheel.kind,
        wheel_labels=wheel.labels,
        wheel_probabilities=tuple(float(value) for value in wheel.probabilities),
    )


def write_spin_csv(dataset: SpinDataset, path: str | PathLike[str]) -> None:
    """Write a ``SpinDataset`` in the strict CSV schema accepted by the reader."""

    if not isinstance(dataset, SpinDataset):
        raise TypeError("dataset must be a SpinDataset.")
    with Path(path).open("w", encoding="utf-8", newline="") as destination:
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(("spin", "pocket"))
        writer.writerows(zip(dataset.spin_indices, dataset.spins, strict=True))
