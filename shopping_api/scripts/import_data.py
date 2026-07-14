"""Validate the Drive-exported shopping CSV and import it into SQLite."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_DIR / "data" / "Shopping_data.csv"
DEFAULT_DATABASE = PROJECT_DIR / "data" / "shopping.db"
DEFAULT_SCHEMA = PROJECT_DIR / "schema.sql"
DEFAULT_SOURCE_URL = (
    "https://drive.google.com/file/d/1-4dSFNppilPVbHeoTeuVS5-CSFMlREFm/view"
)
DEFAULT_SOURCE_MODIFIED_AT = "2026-05-15T20:39:43.000Z"
EXPECTED_HEADERS = (
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
)


class DatasetValidationError(ValueError):
    """Raised when the source file cannot be safely imported."""


def _parse_integer(value: str, *, field: str, row_number: int) -> int:
    try:
        return int(value.strip())
    except (AttributeError, ValueError) as exc:
        raise DatasetValidationError(
            f"Row {row_number}: {field} must be an integer."
        ) from exc


def _parse_rows(source_path: Path) -> list[tuple[str, str, int, int, int]]:
    rows: list[tuple[str, str, int, int, int]] = []
    seen_ids: set[str] = set()

    with source_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        headers = tuple(reader.fieldnames or ())
        if headers != EXPECTED_HEADERS:
            raise DatasetValidationError(
                f"Unexpected CSV headers {headers!r}; expected {EXPECTED_HEADERS!r}."
            )

        for row_number, raw in enumerate(reader, start=2):
            customer_id = raw["CustomerID"].strip()
            if not customer_id or not customer_id.isdigit():
                raise DatasetValidationError(
                    f"Row {row_number}: CustomerID must contain digits."
                )
            if customer_id in seen_ids:
                raise DatasetValidationError(
                    f"Row {row_number}: duplicate CustomerID {customer_id}."
                )
            seen_ids.add(customer_id)

            gender = raw["Genre"].strip().title()
            if gender not in {"Male", "Female"}:
                raise DatasetValidationError(
                    f"Row {row_number}: Genre must be Male or Female."
                )

            age = _parse_integer(raw["Age"], field="Age", row_number=row_number)
            annual_income = _parse_integer(
                raw["Annual Income (k$)"],
                field="Annual Income (k$)",
                row_number=row_number,
            )
            spending_score = _parse_integer(
                raw["Spending Score (1-100)"],
                field="Spending Score (1-100)",
                row_number=row_number,
            )

            if not 0 <= age <= 120:
                raise DatasetValidationError(
                    f"Row {row_number}: Age must be between 0 and 120."
                )
            if annual_income < 0:
                raise DatasetValidationError(
                    f"Row {row_number}: Annual Income must be non-negative."
                )
            if not 1 <= spending_score <= 100:
                raise DatasetValidationError(
                    f"Row {row_number}: Spending Score must be between 1 and 100."
                )

            rows.append(
                (customer_id, gender, age, annual_income, spending_score)
            )

    if not rows:
        raise DatasetValidationError("The source CSV contains no customer rows.")
    return rows


def import_dataset(
    source_path: Path,
    database_path: Path,
    schema_path: Path = DEFAULT_SCHEMA,
    *,
    source_url: str = DEFAULT_SOURCE_URL,
    source_modified_at: str | None = DEFAULT_SOURCE_MODIFIED_AT,
) -> int:
    """Import a validated, complete CSV snapshot and return its row count."""

    rows = _parse_rows(source_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        connection.execute("DELETE FROM customers")
        connection.executemany(
            """
            INSERT INTO customers (
                customer_id, gender, age, annual_income_kusd, spending_score
            ) VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.execute(
            """
            INSERT INTO dataset_metadata (
                singleton_id, source_file, source_url, source_modified_at,
                imported_at, record_count
            ) VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(singleton_id) DO UPDATE SET
                source_file = excluded.source_file,
                source_url = excluded.source_url,
                source_modified_at = excluded.source_modified_at,
                imported_at = excluded.imported_at,
                record_count = excluded.record_count
            """,
            (
                source_path.name,
                source_url,
                source_modified_at,
                datetime.now(UTC).isoformat(),
                len(rows),
            ),
        )

    return len(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument(
        "--source-modified-at", default=DEFAULT_SOURCE_MODIFIED_AT
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    count = import_dataset(
        args.source,
        args.database,
        args.schema,
        source_url=args.source_url,
        source_modified_at=args.source_modified_at,
    )
    print(f"Imported {count} customers into {args.database}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
