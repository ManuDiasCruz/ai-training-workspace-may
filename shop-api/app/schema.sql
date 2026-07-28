-- Shop API - SQLite schema
--
-- The source dataset (Shopping_data.csv) is a single flat table of mall
-- customers, so a single-table design is the honest fit. Segment labels
-- (age bracket / income band / spending tier) are GENERATED ... STORED
-- columns so they are computed by the database itself and can never drift
-- out of sync with the raw values they derive from.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    -- Numeric form of the source CustomerID ("0007" -> 7).
    id              INTEGER PRIMARY KEY,
    -- Zero-padded source identifier, kept verbatim for traceability.
    customer_ref    TEXT    NOT NULL UNIQUE,
    gender          TEXT    NOT NULL CHECK (gender IN ('Female', 'Male')),
    age             INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    -- Annual income in thousands of dollars, as published in the CSV.
    annual_income_k INTEGER NOT NULL CHECK (annual_income_k >= 0),
    spending_score  INTEGER NOT NULL CHECK (spending_score BETWEEN 1 AND 100),

    age_bracket TEXT GENERATED ALWAYS AS (
        CASE
            WHEN age < 25 THEN 'under-25'
            WHEN age < 35 THEN '25-34'
            WHEN age < 45 THEN '35-44'
            WHEN age < 55 THEN '45-54'
            ELSE '55-plus'
        END
    ) STORED,

    income_band TEXT GENERATED ALWAYS AS (
        CASE
            WHEN annual_income_k < 40 THEN 'low'
            WHEN annual_income_k < 80 THEN 'medium'
            ELSE 'high'
        END
    ) STORED,

    spending_tier TEXT GENERATED ALWAYS AS (
        CASE
            WHEN spending_score < 35 THEN 'low'
            WHEN spending_score < 65 THEN 'medium'
            ELSE 'high'
        END
    ) STORED
);

CREATE INDEX IF NOT EXISTS idx_customers_gender         ON customers (gender);
CREATE INDEX IF NOT EXISTS idx_customers_age            ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_income         ON customers (annual_income_k);
CREATE INDEX IF NOT EXISTS idx_customers_spending       ON customers (spending_score);
CREATE INDEX IF NOT EXISTS idx_customers_income_band    ON customers (income_band);
CREATE INDEX IF NOT EXISTS idx_customers_spending_tier  ON customers (spending_tier);
CREATE INDEX IF NOT EXISTS idx_customers_age_bracket    ON customers (age_bracket);

-- Provenance of every import, so a database file can always be traced back
-- to the exact CSV bytes it was built from.
CREATE TABLE IF NOT EXISTS import_runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file   TEXT    NOT NULL,
    source_sha256 TEXT    NOT NULL,
    rows_read     INTEGER NOT NULL,
    rows_imported INTEGER NOT NULL,
    rows_rejected INTEGER NOT NULL,
    imported_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
