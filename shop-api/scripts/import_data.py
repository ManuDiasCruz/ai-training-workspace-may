#!/usr/bin/env python3
"""Import Shopping_data.csv into the local SQLite database.

Idempotent: re-running replaces the table contents rather than appending, so the
row count stays at 200 no matter how many times it is invoked.

Usage:
    python scripts/import_data.py                # default paths
    python scripts/import_data.py --csv other.csv --db /tmp/shop.db
    python scripts/import_data.py --force        # reimport even if unchanged
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running this file directly (python scripts/import_data.py) by putting
# the project root on sys.path so `app` is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config, db  # noqa: E402

#: Source CSV header -> database column.
COLUMN_MAP = {
    "CustomerID": "customer_id",
    "Genre": "gender",
    "Age": "age",
    "Annual Income (k$)": "annual_income_k",
    "Spending Score (1-100)": "spending_score",
}

VALID_GENDERS = {"Male", "Female"}


class DatasetError(ValueError):
    """The source CSV does not match the expected structure."""


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_rows(path: Path) -> list[dict[str, object]]:
    """Read and validate the CSV, returning rows ready for insertion.

    Validation happens here, before the database is touched, so a malformed file
    fails without leaving a half-imported table.
    """
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        missing = [column for column in COLUMN_MAP if column not in headers]
        if missing:
            raise DatasetError(
                f"{path.name} is missing expected column(s): {', '.join(missing)}. "
                f"Found: {', '.join(headers)}"
            )

        rows: list[dict[str, object]] = []
        seen_ids: set[int] = set()
        for line_number, raw in enumerate(reader, start=2):  # line 1 is the header
            try:
                rows.append(_parse_row(raw, seen_ids))
            except DatasetError as exc:
                raise DatasetError(f"{path.name} line {line_number}: {exc}") from exc

    if not rows:
        raise DatasetError(f"{path.name} contains a header but no data rows.")
    return rows


def _parse_row(raw: dict[str, str], seen_ids: set[int]) -> dict[str, object]:
    source_id = (raw["CustomerID"] or "").strip()
    if not source_id.isdigit():
        raise DatasetError(f"CustomerID {source_id!r} is not numeric")
    numeric_id = int(source_id)
    if numeric_id in seen_ids:
        raise DatasetError(f"duplicate CustomerID {source_id!r}")
    seen_ids.add(numeric_id)

    gender = (raw["Genre"] or "").strip()
    if gender not in VALID_GENDERS:
        raise DatasetError(
            f"Genre {gender!r} is not one of {sorted(VALID_GENDERS)}"
        )

    numbers: dict[str, int] = {}
    for header in ("Age", "Annual Income (k$)", "Spending Score (1-100)"):
        value = (raw[header] or "").strip()
        if not value.isdigit():
            raise DatasetError(f"{header} {value!r} is not a non-negative integer")
        numbers[COLUMN_MAP[header]] = int(value)

    if not 1 <= numbers["spending_score"] <= 100:
        raise DatasetError(
            f"Spending Score {numbers['spending_score']} is outside 1-100"
        )

    return {
        "id": numeric_id,
        # Preserve the source's zero-padded width (0001), normalising anything
        # narrower so the stored ids are uniform.
        "customer_id": source_id.zfill(4),
        "gender": gender,
        **numbers,
    }


def import_dataset(csv_file: Path, db_file: Path, *, force: bool = False) -> dict:
    """Create the schema if needed and load the CSV. Returns a short report."""
    if not csv_file.exists():
        raise DatasetError(f"Dataset not found: {csv_file}")

    rows = parse_rows(csv_file)
    checksum = sha256_of(csv_file)

    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    try:
        db.init_schema(conn)

        previous = conn.execute(
            "SELECT source_sha256, row_count FROM import_metadata WHERE id = 1"
        ).fetchone()
        if previous and previous["source_sha256"] == checksum and not force:
            return {
                "skipped": True,
                "row_count": previous["row_count"],
                "sha256": checksum,
            }

        with conn:  # single transaction: all rows land, or none do
            conn.execute("DELETE FROM customers")
            conn.executemany(
                """
                INSERT INTO customers
                    (id, customer_id, gender, age, annual_income_k, spending_score)
                VALUES
                    (:id, :customer_id, :gender, :age, :annual_income_k,
                     :spending_score)
                """,
                rows,
            )
            conn.execute(
                """
                INSERT INTO import_metadata
                    (id, source_file, source_sha256, row_count, imported_at)
                VALUES (1, :source_file, :sha, :count, :at)
                ON CONFLICT(id) DO UPDATE SET
                    source_file   = excluded.source_file,
                    source_sha256 = excluded.source_sha256,
                    row_count     = excluded.row_count,
                    imported_at   = excluded.imported_at
                """,
                {
                    "source_file": csv_file.name,
                    "sha": checksum,
                    "count": len(rows),
                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                },
            )
    finally:
        conn.close()

    return {"skipped": False, "row_count": len(rows), "sha256": checksum}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, default=config.csv_path())
    parser.add_argument("--db", type=Path, default=config.db_path())
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reimport even when the CSV checksum is unchanged",
    )
    args = parser.parse_args(argv)

    try:
        report = import_dataset(args.csv, args.db, force=args.force)
    except DatasetError as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1

    verb = "already up to date" if report["skipped"] else "imported"
    print(f"{args.csv.name} {verb}: {report['row_count']} rows -> {args.db}")
    print(f"  sha256: {report['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
