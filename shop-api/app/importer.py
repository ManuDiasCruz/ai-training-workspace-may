"""Import Shopping_data.csv into the local SQLite database.

Run as a module:

    python -m app.importer                    # import into the default DB
    python -m app.importer --csv other.csv    # import a different file
    python -m app.importer --reset            # drop existing rows first

The import is idempotent: re-running it upserts by customer id, so the row
count stays at 200 no matter how many times it is executed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .config import get_settings
from .db import connect, init_schema
from .models import CustomerRow

# Source header -> internal field name.
COLUMN_MAP = {
    "CustomerID": "customer_ref",
    "Genre": "gender",
    "Age": "age",
    "Annual Income (k$)": "annual_income_k",
    "Spending Score (1-100)": "spending_score",
}

UPSERT_SQL = """
INSERT INTO customers (id, customer_ref, gender, age, annual_income_k, spending_score)
VALUES (:id, :customer_ref, :gender, :age, :annual_income_k, :spending_score)
ON CONFLICT (id) DO UPDATE SET
    customer_ref    = excluded.customer_ref,
    gender          = excluded.gender,
    age             = excluded.age,
    annual_income_k = excluded.annual_income_k,
    spending_score  = excluded.spending_score
"""


@dataclass
class ImportReport:
    rows_read: int = 0
    rows_imported: int = 0
    rejects: list[tuple[int, str]] = field(default_factory=list)

    @property
    def rows_rejected(self) -> int:
        return len(self.rejects)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_row(raw: dict[str, str]) -> CustomerRow:
    """Map one CSV row onto a validated CustomerRow.

    Raises ValueError with a human-readable message for anything unusable.
    """
    missing = [column for column in COLUMN_MAP if raw.get(column) is None]
    if missing:
        raise ValueError(f"missing column(s): {', '.join(missing)}")

    values = {field_name: (raw[column] or "").strip() for column, field_name in COLUMN_MAP.items()}

    ref = values["customer_ref"]
    if not ref.isdigit():
        raise ValueError(f"CustomerID {ref!r} is not numeric")

    for numeric_field in ("age", "annual_income_k", "spending_score"):
        if not values[numeric_field].lstrip("-").isdigit():
            raise ValueError(f"{numeric_field} {values[numeric_field]!r} is not an integer")

    try:
        return CustomerRow(
            id=int(ref),
            customer_ref=ref,
            gender=values["gender"],
            age=int(values["age"]),
            annual_income_k=int(values["annual_income_k"]),
            spending_score=int(values["spending_score"]),
        )
    except ValidationError as exc:
        problems = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors())
        raise ValueError(problems) from exc


def import_csv(
    conn: sqlite3.Connection,
    csv_path: Path,
    *,
    reset: bool = False,
) -> ImportReport:
    """Load csv_path into an already-initialised database."""
    if not csv_path.exists():
        raise FileNotFoundError(f"dataset not found: {csv_path}")

    report = ImportReport()

    # utf-8-sig transparently strips a byte-order mark if the CSV has one.
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path} is empty")

        unknown = set(COLUMN_MAP) - {(name or "").strip() for name in reader.fieldnames}
        if unknown:
            raise ValueError(
                f"{csv_path} is missing expected column(s): {', '.join(sorted(unknown))}"
            )

        if reset:
            conn.execute("DELETE FROM customers")

        seen: set[int] = set()
        for line_no, raw in enumerate(reader, start=2):  # line 1 is the header
            report.rows_read += 1
            try:
                row = parse_row(raw)
            except ValueError as exc:
                report.rejects.append((line_no, str(exc)))
                continue

            if row.id in seen:
                report.rejects.append((line_no, f"duplicate CustomerID {row.customer_ref}"))
                continue
            seen.add(row.id)

            payload = row.model_dump()
            payload["gender"] = row.gender.value
            conn.execute(UPSERT_SQL, payload)
            report.rows_imported += 1

    conn.execute(
        """
        INSERT INTO import_runs (source_file, source_sha256, rows_read, rows_imported, rows_rejected)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            str(csv_path),
            sha256_of(csv_path),
            report.rows_read,
            report.rows_imported,
            report.rows_rejected,
        ),
    )
    conn.commit()
    return report


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Import the shopping dataset into SQLite.")
    parser.add_argument("--csv", type=Path, default=settings.csv_path, help="source CSV file")
    parser.add_argument("--db", type=Path, default=settings.db_path, help="target SQLite file")
    parser.add_argument("--reset", action="store_true", help="delete existing customers first")
    args = parser.parse_args(argv)

    conn = connect(args.db)
    try:
        init_schema(conn)
        report = import_csv(conn, args.csv, reset=args.reset)
        total = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    except (FileNotFoundError, ValueError) as exc:
        print(f"import failed: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()

    print(f"source     : {args.csv}")
    print(f"database   : {args.db}")
    print(f"rows read  : {report.rows_read}")
    print(f"imported   : {report.rows_imported}")
    print(f"rejected   : {report.rows_rejected}")
    for line_no, reason in report.rejects:
        print(f"  line {line_no}: {reason}", file=sys.stderr)
    print(f"customers in database: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
