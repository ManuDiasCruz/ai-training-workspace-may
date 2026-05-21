from __future__ import annotations

import csv
from pathlib import Path

from .config import get_csv_path, get_db_path
from .database import connect, create_schema, customer_count


HEADER_MAP = {
    "customerid": "customer_id",
    "customer id": "customer_id",
    "genre": "genre",
    "gender": "genre",
    "age": "age",
    "annual income (k$)": "annual_income_k",
    "annual income": "annual_income_k",
    "annual_income_k": "annual_income_k",
    "spending score (1-100)": "spending_score",
    "spending score": "spending_score",
    "spending_score": "spending_score",
}
REQUIRED_FIELDS = {
    "customer_id",
    "genre",
    "age",
    "annual_income_k",
    "spending_score",
}


def _normalize_header(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").split())


def _normalize_genre(value: str) -> str:
    normalized = value.strip().capitalize()
    if normalized not in {"Male", "Female"}:
        raise ValueError(f"invalid genre '{value}'")
    return normalized


def _parse_int(value: str, field_name: str, row_number: int) -> int:
    try:
        return int(value.strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"row {row_number}: {field_name} must be an integer (got {value!r})"
        ) from exc


def _parse_row(row: dict[str, str], row_number: int) -> tuple[str, str, int, int, int]:
    customer_id = str(row["customer_id"]).strip()
    if not customer_id:
        raise ValueError(f"row {row_number}: customer_id is required")

    genre = _normalize_genre(row["genre"])
    age = _parse_int(row["age"], "age", row_number)
    annual_income_k = _parse_int(row["annual_income_k"], "annual_income_k", row_number)
    spending_score = _parse_int(row["spending_score"], "spending_score", row_number)

    if age < 0 or age > 120:
        raise ValueError(f"row {row_number}: age must be between 0 and 120")
    if annual_income_k < 0:
        raise ValueError(f"row {row_number}: annual_income_k must be >= 0")
    if spending_score < 0 or spending_score > 100:
        raise ValueError(f"row {row_number}: spending_score must be between 0 and 100")

    return customer_id, genre, age, annual_income_k, spending_score


def read_csv_rows(csv_path: Path) -> list[tuple[str, str, int, int, int]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row")

        normalized_headers = {}
        for header in reader.fieldnames:
            canonical = HEADER_MAP.get(_normalize_header(header))
            if canonical is not None:
                normalized_headers[header] = canonical

        if set(normalized_headers.values()) != REQUIRED_FIELDS:
            raise ValueError(
                "CSV headers do not match expected shopping schema. "
                "Expected CustomerID, Genre, Age, Annual Income (k$), "
                "and Spending Score (1-100)."
            )

        rows = []
        for row_number, raw_row in enumerate(reader, start=2):
            normalized_row = {
                canonical: raw_row[original]
                for original, canonical in normalized_headers.items()
            }
            rows.append(_parse_row(normalized_row, row_number))
        return rows


def import_csv(
    csv_path: Path | None = None,
    db_path: Path | None = None,
    replace: bool = True,
) -> int:
    resolved_csv_path = Path(csv_path or get_csv_path())
    resolved_db_path = Path(db_path or get_db_path())
    parsed_rows = read_csv_rows(resolved_csv_path)
    create_schema(resolved_db_path)

    insert_sql = """
        INSERT INTO customers (
            customer_id,
            genre,
            age,
            annual_income_k,
            spending_score
        )
        VALUES (?, ?, ?, ?, ?)
    """

    with connect(resolved_db_path) as connection:
        if replace:
            connection.execute("DELETE FROM customers")
        connection.executemany(insert_sql, parsed_rows)
        connection.commit()
    return len(parsed_rows)


def ensure_seeded() -> None:
    if customer_count() > 0:
        return
    csv_path = get_csv_path()
    if not csv_path.exists():
        raise FileNotFoundError(
            f"No customers found in the database and no CSV is available at {csv_path}"
        )
    import_csv(csv_path=csv_path, db_path=get_db_path(), replace=True)


def main() -> None:
    imported = import_csv()
    print(f"Imported {imported} shopping customers into {get_db_path()}")


if __name__ == "__main__":
    main()
