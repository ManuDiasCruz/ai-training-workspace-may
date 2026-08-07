"""Import Shopping_data.csv into the local SQLite database.

Usage
-----
    python -m scripts.import_dataset                 # data/Shopping_data.csv -> data/shopping.db
    python -m scripts.import_dataset --csv other.csv --db /tmp/other.db
    python -m scripts.import_dataset --skip-invalid   # report bad rows instead of aborting

Semantics
---------
The CSV is a full snapshot, not a stream of deltas, so an import *replaces*
the contents of the customers table. Running the importer twice therefore
leaves the database in the same state as running it once (idempotent), and
the whole load happens in one transaction: either every row lands or none do
and the previous contents are left untouched.

By default a single invalid row aborts the import. Silently dropping records
from a dataset load is how row counts quietly stop matching the source, so
skipping has to be asked for explicitly with --skip-invalid.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app import config, db

# CSV header -> database column. The source headers carry spaces, parentheses
# and a currency symbol, none of which belong in a column name.
COLUMN_MAP = {
    "CustomerID": "customer_id",
    "Genre": "genre",
    "Age": "age",
    "Annual Income (k$)": "annual_income_k",
    "Spending Score (1-100)": "spending_score",
}

VALID_GENRES = {"Male", "Female"}

# Bounds mirror the CHECK constraints in app/schema.sql. Validating here as
# well turns a constraint violation into a message that names the offending
# line and column instead of a bare IntegrityError.
AGE_RANGE = (0, 120)
SPENDING_SCORE_RANGE = (1, 100)


class ImportError_(Exception):
    """Raised when the import cannot proceed."""


@dataclass(frozen=True)
class CustomerRow:
    customer_id: str
    genre: str
    age: int
    annual_income_k: int
    spending_score: int


@dataclass
class ImportReport:
    source_file: Path
    source_sha256: str
    rows_read: int
    rows_imported: int
    rows_rejected: int
    errors: list[str]
    imported_at: str

    def render(self) -> str:
        lines = [
            "Import complete",
            f"  source        : {self.source_file}",
            f"  sha256        : {self.source_sha256}",
            f"  rows read     : {self.rows_read}",
            f"  rows imported : {self.rows_imported}",
            f"  rows rejected : {self.rows_rejected}",
            f"  imported at   : {self.imported_at}",
        ]
        if self.errors:
            lines.append(f"  rejected rows ({len(self.errors)}):")
            lines.extend(f"    - {err}" for err in self.errors)
        return "\n".join(lines)


def _parse_bounded_int(value: str, field: str, low: int, high: int | None) -> int:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field} is empty")
    try:
        number = int(text)
    except ValueError:
        raise ValueError(f"{field} is not an integer: {text!r}") from None
    if number < low or (high is not None and number > high):
        upper = high if high is not None else "∞"
        raise ValueError(f"{field} out of range [{low}..{upper}]: {number}")
    return number


def parse_row(raw: dict[str, str]) -> CustomerRow:
    """Validate and normalise one CSV row. Raises ValueError if unusable."""
    customer_id = (raw.get("CustomerID") or "").strip()
    if not customer_id.isdigit():
        raise ValueError(f"CustomerID is not numeric: {customer_id!r}")
    if len(customer_id) > 4:
        raise ValueError(f"CustomerID wider than 4 digits: {customer_id!r}")
    # Zero-pad so "1" and "0001" resolve to the same identifier, matching the
    # fixed-width form the schema requires.
    customer_id = customer_id.zfill(4)

    genre = (raw.get("Genre") or "").strip().title()
    if genre not in VALID_GENRES:
        raise ValueError(
            f"Genre must be one of {sorted(VALID_GENRES)}: {(raw.get('Genre') or '').strip()!r}"
        )

    return CustomerRow(
        customer_id=customer_id,
        genre=genre,
        age=_parse_bounded_int(raw.get("Age", ""), "Age", *AGE_RANGE),
        annual_income_k=_parse_bounded_int(
            raw.get("Annual Income (k$)", ""), "Annual Income (k$)", 0, None
        ),
        spending_score=_parse_bounded_int(
            raw.get("Spending Score (1-100)", ""),
            "Spending Score (1-100)",
            *SPENDING_SCORE_RANGE,
        ),
    )


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(csv_file: Path, *, skip_invalid: bool) -> tuple[list[CustomerRow], list[str], int]:
    """Parse the CSV into validated rows plus a list of rejection messages."""
    if not csv_file.exists():
        raise ImportError_(f"CSV not found: {csv_file}")

    # utf-8-sig transparently strips a BOM if a spreadsheet tool added one.
    with csv_file.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)

        missing = [column for column in COLUMN_MAP if column not in (reader.fieldnames or [])]
        if missing:
            raise ImportError_(
                f"CSV is missing required column(s): {', '.join(missing)}. "
                f"Found: {reader.fieldnames}"
            )

        rows: list[CustomerRow] = []
        errors: list[str] = []
        seen: dict[str, int] = {}
        rows_read = 0

        # start=2 because line 1 is the header, so numbers match a text editor.
        for line_number, raw in enumerate(reader, start=2):
            rows_read += 1
            try:
                row = parse_row(raw)
                if row.customer_id in seen:
                    raise ValueError(
                        f"duplicate CustomerID {row.customer_id!r} "
                        f"(first seen on line {seen[row.customer_id]})"
                    )
                seen[row.customer_id] = line_number
                rows.append(row)
            except ValueError as exc:
                message = f"line {line_number}: {exc}"
                if not skip_invalid:
                    raise ImportError_(
                        f"{message}\nAborting; no rows were written. "
                        "Re-run with --skip-invalid to import the valid rows instead."
                    ) from None
                errors.append(message)

    if not rows:
        raise ImportError_(f"No valid rows found in {csv_file}")

    return rows, errors, rows_read


def import_dataset(
    csv_file: Path | None = None,
    db_file: Path | None = None,
    *,
    skip_invalid: bool = False,
) -> ImportReport:
    """Load the CSV into SQLite, replacing any previously imported rows."""
    csv_file = Path(csv_file) if csv_file is not None else config.csv_path()
    db_file = Path(db_file) if db_file is not None else config.db_path()

    rows, errors, rows_read = read_rows(csv_file, skip_invalid=skip_invalid)
    checksum = sha256_of(csv_file)
    imported_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    conn = db.connect(db_file)
    try:
        db.apply_schema(conn)
        try:
            # One transaction: a failure part-way through rolls back to the
            # previously imported snapshot rather than leaving a partial load.
            with conn:
                conn.execute("DELETE FROM customers")
                conn.executemany(
                    """
                    INSERT INTO customers
                        (customer_id, genre, age, annual_income_k, spending_score)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (r.customer_id, r.genre, r.age, r.annual_income_k, r.spending_score)
                        for r in rows
                    ],
                )
                conn.execute(
                    """
                    INSERT INTO import_runs
                        (source_file, source_sha256, row_count, imported_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (str(csv_file), checksum, len(rows), imported_at),
                )
        except sqlite3.IntegrityError as exc:
            raise ImportError_(
                f"Database rejected the data: {exc}. No rows were written."
            ) from exc
    finally:
        conn.close()

    return ImportReport(
        source_file=csv_file,
        source_sha256=checksum,
        rows_read=rows_read,
        rows_imported=len(rows),
        rows_rejected=len(errors),
        errors=errors,
        imported_at=imported_at,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.import_dataset",
        description="Import the shopping dataset CSV into the local SQLite database.",
    )
    parser.add_argument("--csv", type=Path, default=None, help="Source CSV (default: data/Shopping_data.csv)")
    parser.add_argument("--db", type=Path, default=None, help="Target database (default: data/shopping.db)")
    parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Import valid rows and report invalid ones instead of aborting.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = import_dataset(args.csv, args.db, skip_invalid=args.skip_invalid)
    except ImportError_ as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(report.render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
