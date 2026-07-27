from __future__ import annotations

import argparse
import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from app.database import DEFAULT_DATABASE_PATH, PROJECT_ROOT, connect, initialize_database


DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "Shopping_data.csv"
REQUIRED_COLUMNS = {
    "CustomerID",
    "Genre",
    "Age",
    "Annual Income (k$)",
    "Spending Score (1-100)",
}


class DataImportError(ValueError):
    """Raised when a source row cannot be safely persisted."""


@dataclass(frozen=True)
class CustomerRecord:
    customer_id: str
    genre: str
    age: int
    annual_income_k: int
    spending_score: int


@dataclass(frozen=True)
class ImportResult:
    rows_imported: int
    rows_in_database: int
    database_path: Path
    source_sha256: str


def _integer(
    row: dict[str, str],
    column: str,
    row_number: int,
    *,
    minimum: int,
    maximum: int | None = None,
) -> int:
    try:
        value = int(row[column])
    except (KeyError, TypeError, ValueError) as exc:
        raise DataImportError(
            f"Row {row_number}: {column!r} must be an integer."
        ) from exc

    if value < minimum or (maximum is not None and value > maximum):
        upper = f" and {maximum}" if maximum is not None else ""
        raise DataImportError(
            f"Row {row_number}: {column!r} must be between {minimum}{upper}."
        )
    return value


def read_records(csv_path: Path | str) -> Iterator[CustomerRecord]:
    path = Path(csv_path)
    if not path.is_file():
        raise DataImportError(f"Dataset not found: {path}")

    seen_ids: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing:
            raise DataImportError(
                "Dataset is missing required columns: " + ", ".join(sorted(missing))
            )

        for row_number, row in enumerate(reader, start=2):
            customer_id = (row.get("CustomerID") or "").strip()
            if not re.fullmatch(r"\d{4}", customer_id):
                raise DataImportError(
                    f"Row {row_number}: CustomerID must contain exactly four digits."
                )
            if customer_id in seen_ids:
                raise DataImportError(
                    f"Row {row_number}: duplicate CustomerID {customer_id!r}."
                )
            seen_ids.add(customer_id)

            genre = (row.get("Genre") or "").strip().title()
            if genre not in {"Male", "Female"}:
                raise DataImportError(
                    f"Row {row_number}: Genre must be 'Male' or 'Female'."
                )

            yield CustomerRecord(
                customer_id=customer_id,
                genre=genre,
                age=_integer(row, "Age", row_number, minimum=0, maximum=120),
                annual_income_k=_integer(
                    row, "Annual Income (k$)", row_number, minimum=0
                ),
                spending_score=_integer(
                    row,
                    "Spending Score (1-100)",
                    row_number,
                    minimum=1,
                    maximum=100,
                ),
            )


def import_csv(
    csv_path: Path | str = DEFAULT_CSV_PATH,
    database_path: Path | str = DEFAULT_DATABASE_PATH,
) -> ImportResult:
    source_path = Path(csv_path)
    target_path = initialize_database(database_path)
    records = list(read_records(source_path))
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()

    with connect(target_path) as connection:
        connection.executemany(
            """
            INSERT INTO customers (
                customer_id, genre, age, annual_income_k, spending_score
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(customer_id) DO UPDATE SET
                genre = excluded.genre,
                age = excluded.age,
                annual_income_k = excluded.annual_income_k,
                spending_score = excluded.spending_score,
                imported_at = CURRENT_TIMESTAMP
            """,
            [
                (
                    record.customer_id,
                    record.genre,
                    record.age,
                    record.annual_income_k,
                    record.spending_score,
                )
                for record in records
            ],
        )
        connection.execute(
            """
            INSERT INTO dataset_imports (
                source_file, source_sha256, rows_imported
            ) VALUES (?, ?, ?)
            """,
            (source_path.name, source_sha256, len(records)),
        )
        rows_in_database = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

    return ImportResult(
        rows_imported=len(records),
        rows_in_database=rows_in_database,
        database_path=target_path,
        source_sha256=source_sha256,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate and import the shopping CSV into SQLite."
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE_PATH)
    args = parser.parse_args()

    result = import_csv(args.csv, args.database)
    print(
        f"Imported {result.rows_imported} rows into {result.database_path} "
        f"({result.rows_in_database} rows total)."
    )


if __name__ == "__main__":
    main()
