"""Tests for the CSV -> SQLite importer."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.import_dataset import ImportError_, import_dataset

HEADER = "CustomerID,Genre,Age,Annual Income (k$),Spending Score (1-100)"


def write_csv(path: Path, *rows: str) -> Path:
    path.write_text("\n".join([HEADER, *rows]) + "\n", encoding="utf-8")
    return path


def count_customers(db_file: Path) -> int:
    conn = sqlite3.connect(db_file)
    try:
        return conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    finally:
        conn.close()


def test_imports_the_full_dataset(test_db: Path) -> None:
    assert count_customers(test_db) == 200


def test_reimport_replaces_rather_than_duplicates(tmp_path: Path) -> None:
    """The CSV is a snapshot, so importing twice must leave one copy."""
    csv_file = write_csv(tmp_path / "in.csv", "0001,Male,19,15,39", "0002,Female,21,16,81")
    db_file = tmp_path / "out.db"

    import_dataset(csv_file, db_file)
    second = import_dataset(csv_file, db_file)

    assert second.rows_imported == 2
    assert count_customers(db_file) == 2


def test_short_identifiers_are_zero_padded(tmp_path: Path) -> None:
    csv_file = write_csv(tmp_path / "in.csv", "7,Male,19,15,39")
    db_file = tmp_path / "out.db"

    import_dataset(csv_file, db_file)

    conn = sqlite3.connect(db_file)
    try:
        assert conn.execute("SELECT customer_id FROM customers").fetchone()[0] == "0007"
    finally:
        conn.close()


def test_genre_is_normalised(tmp_path: Path) -> None:
    csv_file = write_csv(tmp_path / "in.csv", "0001,  female ,19,15,39")
    db_file = tmp_path / "out.db"

    import_dataset(csv_file, db_file)

    conn = sqlite3.connect(db_file)
    try:
        assert conn.execute("SELECT genre FROM customers").fetchone()[0] == "Female"
    finally:
        conn.close()


@pytest.mark.parametrize(
    ("row", "expected_message"),
    [
        ("ABCD,Male,19,15,39", "not numeric"),
        ("0001,Alien,19,15,39", "Genre must be one of"),
        ("0001,Male,999,15,39", "out of range"),
        ("0001,Male,19,15,0", "out of range"),
        ("0001,Male,,15,39", "is empty"),
        ("0001,Male,nineteen,15,39", "not an integer"),
    ],
)
def test_invalid_row_aborts_the_import(
    tmp_path: Path, row: str, expected_message: str
) -> None:
    """Bad data must stop the load rather than be dropped silently."""
    csv_file = write_csv(tmp_path / "in.csv", row)
    db_file = tmp_path / "out.db"

    with pytest.raises(ImportError_, match=expected_message):
        import_dataset(csv_file, db_file)


def test_abort_leaves_previous_data_intact(tmp_path: Path) -> None:
    """A failed import must not destroy the snapshot already in the database."""
    db_file = tmp_path / "out.db"
    good = write_csv(tmp_path / "good.csv", "0001,Male,19,15,39", "0002,Female,21,16,81")
    import_dataset(good, db_file)

    bad = write_csv(tmp_path / "bad.csv", "0003,Male,22,20,50", "0004,Martian,30,40,60")
    with pytest.raises(ImportError_):
        import_dataset(bad, db_file)

    conn = sqlite3.connect(db_file)
    try:
        ids = [row[0] for row in conn.execute("SELECT customer_id FROM customers ORDER BY 1")]
    finally:
        conn.close()
    assert ids == ["0001", "0002"], "the earlier snapshot should be untouched"


def test_skip_invalid_imports_the_rest_and_reports(tmp_path: Path) -> None:
    csv_file = write_csv(
        tmp_path / "in.csv",
        "0001,Male,19,15,39",
        "0002,Klingon,21,16,81",
        "0003,Female,20,16,6",
    )
    db_file = tmp_path / "out.db"

    report = import_dataset(csv_file, db_file, skip_invalid=True)

    assert report.rows_read == 3
    assert report.rows_imported == 2
    assert report.rows_rejected == 1
    # The message points at the offending line in the file.
    assert "line 3" in report.errors[0]
    assert count_customers(db_file) == 2


def test_duplicate_identifier_is_detected(tmp_path: Path) -> None:
    csv_file = write_csv(tmp_path / "in.csv", "0001,Male,19,15,39", "0001,Female,21,16,81")
    db_file = tmp_path / "out.db"

    with pytest.raises(ImportError_, match="duplicate CustomerID"):
        import_dataset(csv_file, db_file)


def test_missing_column_is_reported_by_name(tmp_path: Path) -> None:
    path = tmp_path / "in.csv"
    path.write_text("CustomerID,Genre,Age\n0001,Male,19\n", encoding="utf-8")

    with pytest.raises(ImportError_, match=r"missing required column\(s\).*Annual Income"):
        import_dataset(path, tmp_path / "out.db")


def test_missing_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(ImportError_, match="CSV not found"):
        import_dataset(tmp_path / "absent.csv", tmp_path / "out.db")


def test_empty_csv_is_rejected(tmp_path: Path) -> None:
    path = write_csv(tmp_path / "in.csv")

    with pytest.raises(ImportError_, match="No valid rows"):
        import_dataset(path, tmp_path / "out.db")


def test_report_records_checksum_and_counts(tmp_path: Path) -> None:
    csv_file = write_csv(tmp_path / "in.csv", "0001,Male,19,15,39")

    report = import_dataset(csv_file, tmp_path / "out.db")

    assert report.rows_imported == 1
    assert len(report.source_sha256) == 64
    assert "rows imported : 1" in report.render()


def test_schema_rejects_out_of_domain_writes(test_db: Path) -> None:
    """The CHECK constraints must hold even if a write bypasses the importer."""
    conn = sqlite3.connect(test_db)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO customers VALUES ('0999', 'Other', 30, 50, 50)"
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO customers VALUES ('0999', 'Male', 30, 50, 500)"
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO customers VALUES ('abc', 'Male', 30, 50, 50)")
    finally:
        conn.rollback()
        conn.close()
