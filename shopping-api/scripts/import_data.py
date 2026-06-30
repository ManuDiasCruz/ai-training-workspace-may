"""Load the shopping CSV dataset into the local SQLite database.

Usage
-----
    python -m scripts.import_data            # uses data/Shopping_data.csv
    python -m scripts.import_data path.csv   # custom CSV path

The script is idempotent: it creates the schema if needed and replaces any
existing rows so re-running always yields a clean import.
"""

import csv
import sys
from pathlib import Path

# Allow running both as a module and as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Customer  # noqa: E402

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "data" / "Shopping_data.csv"


def parse_rows(csv_path: Path):
    """Yield validated Customer kwargs from the CSV file."""
    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for line_no, raw in enumerate(reader, start=2):
            # Tolerate stray whitespace in headers/values from the source file.
            row = {k.strip(): (v.strip() if v else v) for k, v in raw.items()}
            try:
                yield {
                    "customer_id": int(row["CustomerID"]),
                    "genre": row["Genre"],
                    "age": int(row["Age"]),
                    "annual_income_k": int(row["Annual Income (k$)"]),
                    "spending_score": int(row["Spending Score (1-100)"]),
                }
            except (KeyError, ValueError) as exc:
                raise ValueError(f"Malformed row at line {line_no}: {raw}") from exc


def import_data(csv_path: Path = DEFAULT_CSV) -> int:
    """Create the schema and load all rows. Returns the number imported."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    Base.metadata.create_all(bind=engine)

    rows = list(parse_rows(csv_path))
    with SessionLocal() as db:
        db.query(Customer).delete()  # fresh, idempotent load
        db.add_all(Customer(**r) for r in rows)
        db.commit()
    return len(rows)


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    count = import_data(path)
    print(f"Imported {count} customer records into the database.")
