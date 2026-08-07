"""Request and response schemas.

Every query parameter the API accepts is declared here as a Pydantic field
with its bounds attached, so validation happens before a request reaches any
SQL and the same declarations generate the OpenAPI documentation.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app import config

# Mirrors the CHECK constraints in app/schema.sql.
AGE_MIN, AGE_MAX = 0, 120
SCORE_MIN, SCORE_MAX = 1, 100

# Boundaries for the derived spending segments reported by /stats. Inclusive.
SEGMENT_BOUNDS = {"low": (1, 33), "medium": (34, 66), "high": (67, 100)}


class Genre(str, Enum):
    male = "Male"
    female = "Female"


class SortField(str, Enum):
    """Sortable columns.

    The values are literal database column names. Membership in this enum is
    what makes them safe to interpolate into an ORDER BY clause, since SQL
    identifiers cannot be supplied as bound parameters.
    """

    customer_id = "customer_id"
    age = "age"
    annual_income_k = "annual_income_k"
    spending_score = "spending_score"
    genre = "genre"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class CustomerQuery(BaseModel):
    """Query parameters for listing customers.

    extra="forbid" makes an unrecognised parameter a 422 rather than a
    silently ignored one, so `?min_agee=30` fails loudly instead of returning
    an unfiltered page that looks correct.
    """

    model_config = ConfigDict(extra="forbid")

    page: int = Field(1, ge=1, le=config.MAX_PAGE, description="1-based page number.")
    page_size: int = Field(
        config.DEFAULT_PAGE_SIZE,
        ge=1,
        le=config.MAX_PAGE_SIZE,
        description=f"Records per page (max {config.MAX_PAGE_SIZE}).",
    )

    genre: Genre | None = Field(None, description="Exact match on genre.")
    min_age: int | None = Field(None, ge=AGE_MIN, le=AGE_MAX, description="Inclusive lower bound on age.")
    max_age: int | None = Field(None, ge=AGE_MIN, le=AGE_MAX, description="Inclusive upper bound on age.")
    min_income: int | None = Field(None, ge=0, description="Inclusive lower bound on annual income (k$).")
    max_income: int | None = Field(None, ge=0, description="Inclusive upper bound on annual income (k$).")
    min_score: int | None = Field(
        None, ge=SCORE_MIN, le=SCORE_MAX, description="Inclusive lower bound on spending score."
    )
    max_score: int | None = Field(
        None, ge=SCORE_MIN, le=SCORE_MAX, description="Inclusive upper bound on spending score."
    )

    q: str | None = Field(
        None,
        min_length=1,
        max_length=50,
        description=(
            "Case-insensitive substring search over the dataset's textual "
            "columns (customer_id and genre)."
        ),
    )

    sort_by: SortField = Field(SortField.customer_id, description="Column to sort by.")
    order: SortOrder = Field(SortOrder.asc, description="Sort direction.")

    @model_validator(mode="after")
    def check_range_coherence(self) -> CustomerQuery:
        """Reject inverted ranges.

        min_age=50&max_age=30 is satisfiable by nothing, so it is far more
        likely a caller mistake than an intentional request for an empty page.
        """
        for low_name, high_name in (
            ("min_age", "max_age"),
            ("min_income", "max_income"),
            ("min_score", "max_score"),
        ):
            low, high = getattr(self, low_name), getattr(self, high_name)
            if low is not None and high is not None and low > high:
                raise ValueError(
                    f"{low_name} ({low}) cannot be greater than {high_name} ({high})"
                )
        return self

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Customer(BaseModel):
    """One dataset record."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_id": "0001",
                "genre": "Male",
                "age": 19,
                "annual_income_k": 15,
                "spending_score": 39,
            }
        }
    )

    customer_id: str = Field(description="Original zero-padded dataset identifier.")
    genre: Genre
    age: int
    annual_income_k: int = Field(description="Annual income in thousands of USD.")
    spending_score: int = Field(description="Spending score, 1 (lowest) to 100 (highest).")


class Pagination(BaseModel):
    page: int
    page_size: int
    total_items: int = Field(description="Total records matching the filters, ignoring pagination.")
    total_pages: int
    has_next: bool
    has_previous: bool


class CustomerPage(BaseModel):
    items: list[Customer]
    pagination: Pagination


class NumericSummary(BaseModel):
    min: int
    max: int
    mean: float


class GenreStat(BaseModel):
    genre: Genre
    count: int
    share_pct: float = Field(description="Percentage of all customers, rounded to 2 decimals.")
    mean_age: float
    mean_annual_income_k: float
    mean_spending_score: float


class SegmentStat(BaseModel):
    segment: str = Field(description="Derived spending band.")
    score_range: str = Field(description="Inclusive spending_score bounds for the band.")
    count: int
    mean_annual_income_k: float


class ImportInfo(BaseModel):
    """Provenance of the data currently being served."""

    source_file: str
    source_sha256: str
    row_count: int
    imported_at: str


class DatasetStats(BaseModel):
    total_customers: int
    genre_breakdown: list[GenreStat]
    age: NumericSummary
    annual_income_k: NumericSummary
    spending_score: NumericSummary
    spending_segments: list[SegmentStat]
    last_import: ImportInfo | None = Field(
        None, description="Null if the database was populated without the importer."
    )


class HealthStatus(BaseModel):
    status: str
    database: str
    customer_count: int
    version: str
