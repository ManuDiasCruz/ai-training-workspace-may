"""Tests for the CSV -> SQLite import path."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.db import connect, init_schema
from app.importer import import_csv

from .conftest import CSV_PATH, TOTAL_ROWS

HEADER = "CustomerID,Genre,Age,Annual Income (k$),Spending Score (1-100)\n"


@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    connection = connect(tmp_path / "import.db")
    init_schema(connection)
    yield connection
    connection.close()


def write_csv(tmp_path: Path, body: str, name: str = "input.csv") -> Path:
    path = tmp_path / name
    path.write_text(HEADER + body, encoding="utf-8")
    return path


def test_imports_every_row_of_the_real_dataset(conn: sqlite3.Connection) -> None:
    report = import_csv(conn, CSV_PATH)
    assert (report.rows_read, report.rows_imported, report.rows_rejected) == (
        TOTAL_ROWS,
        TOTAL_ROWS,
        0,
    )
    assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == TOTAL_ROWS


def test_reimport_is_idempotent(conn: sqlite3.Connection) -> None:
    import_csv(conn, CSV_PATH)
    import_csv(conn, CSV_PATH)
    assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == TOTAL_ROWS
    assert conn.execute("SELECT COUNT(*) FROM import_runs").fetchone()[0] == 2


def test_import_records_source_checksum(conn: sqlite3.Connection) -> None:
    import_csv(conn, CSV_PATH)
    row = conn.execute("SELECT source_sha256, rows_imported FROM import_runs").fetchone()
    assert len(row["source_sha256"]) == 64
    assert row["rows_imported"] == TOTAL_ROWS


def test_bad_rows_are_rejected_without_aborting_the_import(
    conn: sqlite3.Connection, tmp_path: Path
) -> None:
    csv_path = write_csv(
        tmp_path,
        "0001,Male,19,15,39\n"
        "0002,Robot,30,40,50\n"        # gender outside the allowed set
        "0003,Female,not-a-number,40,50\n"
        "0004,Female,30,40,0\n"        # spending score below 1
        "0005,Female,200,40,50\n"      # implausible age
        "abcd,Female,30,40,50\n"       # non-numeric CustomerID
        "0006,Female,30,40,50\n",
    )
    report = import_csv(conn, csv_path)

    assert report.rows_read == 7
    assert report.rows_imported == 2
    assert report.rows_rejected == 5
    assert [line for line, _ in report.rejects] == [3, 4, 5, 6, 7]
    assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 2


def test_duplicate_ids_within_one_file_are_reported(
    conn: sqlite3.Connection, tmp_path: Path
) -> None:
    csv_path = write_csv(tmp_path, "0001,Male,19,15,39\n0001,Female,30,40,50\n")
    report = import_csv(conn, csv_path)
    assert report.rows_imported == 1
    assert "duplicate" in report.rejects[0][1]


def test_gender_casing_is_normalised(conn: sqlite3.Connection, tmp_path: Path) -> None:
    csv_path = write_csv(tmp_path, "0001, male ,19,15,39\n0002,FEMALE,30,40,50\n")
    report = import_csv(conn, csv_path)
    assert report.rows_imported == 2
    assert [row["gender"] for row in conn.execute("SELECT gender FROM customers ORDER BY id")] == [
        "Male",
        "Female",
    ]


def test_reset_clears_previous_rows(conn: sqlite3.Connection, tmp_path: Path) -> None:
    import_csv(conn, CSV_PATH)
    csv_path = write_csv(tmp_path, "0001,Male,19,15,39\n")
    import_csv(conn, csv_path, reset=True)
    assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 1


def test_missing_file_raises(conn: sqlite3.Connection, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        import_csv(conn, tmp_path / "nope.csv")


def test_wrong_headers_raise_before_any_write(conn: sqlite3.Connection, tmp_path: Path) -> None:
    path = tmp_path / "wrong.csv"
    path.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing expected column"):
        import_csv(conn, path)
    assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0


def test_schema_rejects_out_of_range_values_directly(conn: sqlite3.Connection) -> None:
    """The CHECK constraints are a real backstop, not decoration."""
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO customers (id, customer_ref, gender, age, annual_income_k, spending_score)"
            " VALUES (1, '0001', 'Male', 19, 15, 500)"
        )
