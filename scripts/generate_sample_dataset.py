"""Generate a same-schema sample shopping customer dataset.

The repository includes the 200-row Google Drive CSV at data/shopping.csv.
This helper is only for creating a deterministic local substitute when
experimenting with importer behavior.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "shopping.csv"

HEADER = [
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
]
GENRES = ["Female", "Male"]


def generate(n: int = 200, seed: int = 42) -> None:
    rng = random.Random(seed)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for i in range(1, n + 1):
            writer.writerow(
                [
                    f"{i:04d}",
                    rng.choice(GENRES),
                    rng.randint(18, 70),
                    rng.randint(15, 137),
                    rng.randint(1, 100),
                ]
            )
    print(f"Wrote {n} rows to {OUT}")


if __name__ == "__main__":
    generate()
