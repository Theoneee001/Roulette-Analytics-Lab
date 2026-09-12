# Reproducible Spin Examples

`example_unbiased_spins.csv` and `example_biased_spins.csv` are generated files.
Rebuild both with:

```sh
python scripts/run_analysis.py
```

The generator uses NumPy `Generator` instances with the PCG64 bit generator.
Each file contains 1,000 European-wheel spins and the exact two-column CSV schema
`spin,pocket`. `spin` is a unique consecutive positive integer beginning at 1;
`pocket` is the literal wheel label, so the American-wheel label `00` is never
numeric-coerced when this schema is used elsewhere.

| File | Seed | Wheel model |
|---|---:|---|
| `example_unbiased_spins.csv` | `2026091201` | Fair European wheel, each of 37 pockets has probability `1/37`. |
| `example_biased_spins.csv` | `2026091202` | European wheel with pocket `17` probability `0.06`; the remaining `0.94` mass is redistributed proportionally over all other pockets. |

The generator source is `scripts/run_analysis.py`; do not edit data rows by hand.
