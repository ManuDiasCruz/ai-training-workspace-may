-- Schema for the shopping-dataset API.
--
-- Source: Shopping_data.csv (Mall Customers dataset, 200 rows).
-- Source header -> column mapping:
--   CustomerID              -> id (numeric) + customer_id (canonical zero-padded text)
--   Genre                   -> gender          (source header says "Genre" but the
--                                               values are Male/Female, i.e. gender)
--   Annual Income (k$)      -> annual_income_k  (unit kept in the name: thousands of USD)
--   Spending Score (1-100)  -> spending_score

PRAGMA journal_mode = WAL;

-- One row per customer. The dataset is a single flat observation table with no
-- repeating groups, so one table is already in 3NF; splitting the two-value
-- `gender` domain into a lookup table would add a join without removing any
-- redundancy, so it is enforced with a CHECK constraint instead.
CREATE TABLE IF NOT EXISTS customers (
    -- Numeric form of CustomerID (1..200). Used for ordering and lookups; as an
    -- INTEGER PRIMARY KEY this aliases SQLite's rowid, so it costs no extra space.
    id              INTEGER PRIMARY KEY,

    -- Canonical identifier exactly as it appears in the CSV, e.g. '0001'.
    -- Preserved so the API can round-trip the source representation.
    customer_id     TEXT    NOT NULL UNIQUE,

    gender          TEXT    NOT NULL CHECK (gender IN ('Male', 'Female')),
    age             INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score  INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100)
);

-- Indexes cover the fields the API exposes as filters and sort keys. Range
-- filters (age/income/score) and the equality filter (gender) all benefit.
CREATE INDEX IF NOT EXISTS idx_customers_gender ON customers (gender);
CREATE INDEX IF NOT EXISTS idx_customers_age    ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_income ON customers (annual_income_k);
CREATE INDEX IF NOT EXISTS idx_customers_score  ON customers (spending_score);

-- Provenance of the last import: lets /health report what was loaded and lets
-- the importer detect an unchanged source file (see scripts/import_data.py).
CREATE TABLE IF NOT EXISTS import_metadata (
    id              INTEGER PRIMARY KEY CHECK (id = 1),  -- single-row table
    source_file     TEXT    NOT NULL,
    source_sha256   TEXT    NOT NULL,
    row_count       INTEGER NOT NULL,
    imported_at     TEXT    NOT NULL
);

-- Derived read model: adds a coarse marketing segment from the income/spending
-- quadrant. The thresholds are a documented heuristic (see README), NOT a
-- clustering result -- they are kept in the view so the rule lives in one place
-- and can be filtered on directly.
DROP VIEW IF EXISTS customers_enriched;
CREATE VIEW customers_enriched AS
SELECT
    c.id,
    c.customer_id,
    c.gender,
    c.age,
    c.annual_income_k,
    c.spending_score,
    CASE
        WHEN c.annual_income_k <= 40 AND c.spending_score >= 60 THEN 'careless'
        WHEN c.annual_income_k <= 40 AND c.spending_score <= 40 THEN 'frugal'
        WHEN c.annual_income_k >= 70 AND c.spending_score >= 60 THEN 'target'
        WHEN c.annual_income_k >= 70 AND c.spending_score <= 40 THEN 'cautious'
        ELSE 'standard'
    END AS segment
FROM customers c;
