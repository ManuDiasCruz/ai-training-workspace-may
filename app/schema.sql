-- ShopAPI database schema (SQLite).
--
-- This file is the single source of truth for the local database: the
-- importer and the test suite both build their schema by executing it.
--
-- Requires SQLite 3.37+ for STRICT tables (bundled with Python 3.11+).

-- ---------------------------------------------------------------------------
-- customers — one row per record in Shopping_data.csv.
--
-- The source CSV is a flat, fully denormalised file with no repeating groups,
-- so a single table is the correct shape. Splitting `genre` into a lookup
-- table would add a join for a two-value domain with no upside; a CHECK
-- constraint captures the same invariant at a fraction of the cost.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    -- Original dataset identifier, preserved verbatim as fixed-width
    -- zero-padded text ("0001") so the API round-trips the source value.
    -- Because the width is fixed, lexicographic ordering is also numeric
    -- ordering, so ORDER BY customer_id needs no CAST.
    customer_id     TEXT    PRIMARY KEY
                            CHECK (customer_id GLOB '[0-9][0-9][0-9][0-9]'),

    -- The CSV column is named "Genre" but holds gender values. The name is
    -- kept to stay faithful to the source; the domain is closed to the two
    -- values actually present in the data.
    genre           TEXT    NOT NULL
                            CHECK (genre IN ('Male', 'Female')),

    age             INTEGER NOT NULL
                            CHECK (age BETWEEN 0 AND 120),

    -- Annual income in thousands of USD, from "Annual Income (k$)". The unit
    -- is folded into the column name so the value needs no interpretation.
    annual_income_k INTEGER NOT NULL
                            CHECK (annual_income_k >= 0),

    -- Source column "Spending Score (1-100)": a 1..100 index where higher
    -- means more spending.
    spending_score  INTEGER NOT NULL
                            CHECK (spending_score BETWEEN 1 AND 100)
) STRICT;

-- Indexes backing the API's filter and sort parameters. Each one covers a
-- documented query knob; there are no speculative indexes here.
CREATE INDEX IF NOT EXISTS idx_customers_genre          ON customers (genre);
CREATE INDEX IF NOT EXISTS idx_customers_age            ON customers (age);
CREATE INDEX IF NOT EXISTS idx_customers_income         ON customers (annual_income_k);
CREATE INDEX IF NOT EXISTS idx_customers_spending_score ON customers (spending_score);

-- ---------------------------------------------------------------------------
-- import_runs — provenance for each load of the CSV.
--
-- Keeps the answer to "which file produced the rows I am serving, and when?"
-- inside the database instead of in someone's shell history. The SHA-256 of
-- the source file makes a silent dataset swap detectable.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS import_runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file   TEXT    NOT NULL,
    source_sha256 TEXT    NOT NULL,
    row_count     INTEGER NOT NULL,
    -- ISO-8601 UTC timestamp. SQLite has no native date type; text in this
    -- format sorts chronologically.
    imported_at   TEXT    NOT NULL
) STRICT;
