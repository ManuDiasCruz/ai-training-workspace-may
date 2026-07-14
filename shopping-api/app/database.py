"""SQLite helpers: database location, connection factory and schema management."""

import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "shopping.db"

# Column names mirror the CSV header, normalised to snake_case:
#   CustomerID              -> customer_id
#   Genre                   -> genre
#   Age                     -> age
#   Annual Income (k$)      -> annual_income_k
#   Spending Score (1-100)  -> spending_score
SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id     INTEGER PRIMARY KEY,
    genre           TEXT    NOT NULL CHECK (genre IN ('Male', 'Female')),
    age             INTEGER NOT NULL CHECK (age BETWEEN 1 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score  INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_customers_genre  ON customers (genre);
CREATE INDEX IF NOT EXISTS idx_customers_age    ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_income ON customers (annual_income_k);
CREATE INDEX IF NOT EXISTS idx_customers_score  ON customers (spending_score);
"""


def get_db_path() -> Path:
    """Resolve the database path, allowing tests/deployments to override it."""
    return Path(os.environ.get("SHOPPING_DB_PATH", DEFAULT_DB_PATH))


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with row access by column name."""
    path = Path(db_path) if db_path is not None else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create the customers table and its indexes if they do not exist yet."""
    conn.executescript(SCHEMA)
    conn.commit()
