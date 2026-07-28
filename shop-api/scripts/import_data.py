"""Import the shopping CSV dataset into the local SQLite database.

Usage:
    python scripts/import_data.py [path/to/Shopping_data.csv]

Re-running the script replaces existing rows (idempotent import).
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import PROJECT_ROOT, get_connection, init_db

DEFAULT_CSV = PROJECT_ROOT / "data" / "Shopping_data.csv"


def import_csv(csv_path: Path) -> int:
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = [
            (
                int(row["CustomerID"]),
                row["Genre"].strip(),
                int(row["Age"]),
                int(row["Annual Income (k$)"]),
                int(row["Spending Score (1-100)"]),
            )
            for row in reader
        ]

    conn = get_connection()
    try:
        init_db(conn)
        conn.execute("DELETE FROM customers")
        conn.executemany(
            "INSERT INTO customers (customer_id, genre, age, annual_income, spending_score)"
            " VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()
    return len(rows)


if __name__ == "__main__":
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    count = import_csv(csv_path)
    print(f"Imported {count} customers from {csv_path}")
