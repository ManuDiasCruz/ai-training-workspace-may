PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    gender TEXT NOT NULL CHECK (gender IN ('Male', 'Female')),
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_kusd INTEGER NOT NULL CHECK (annual_income_kusd >= 0),
    spending_score INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_customers_gender ON customers (gender);
CREATE INDEX IF NOT EXISTS idx_customers_age ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_annual_income
    ON customers (annual_income_kusd);
CREATE INDEX IF NOT EXISTS idx_customers_spending_score
    ON customers (spending_score);

CREATE TABLE IF NOT EXISTS dataset_metadata (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    source_file TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_modified_at TEXT,
    imported_at TEXT NOT NULL,
    record_count INTEGER NOT NULL CHECK (record_count >= 0)
);
