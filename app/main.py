from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import Base, engine, get_db


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title="Shopping Customers API",
        version="1.0.0",
        description=(
            "REST API exposing the Mall Customer Segmentation dataset "
            "(CustomerID, Gender, Age, Annual Income, Spending Score)."
        ),
    )

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    @app.get("/stats", response_model=schemas.StatsOut, tags=["customers"])
    def get_stats(db: Session = Depends(get_db)):
        return crud.stats(db)

    @app.get(
        "/customers",
        response_model=schemas.PaginatedCustomers,
        tags=["customers"],
    )
    def list_customers(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=200),
        gender: Optional[schemas.Gender] = None,
        min_age: Optional[int] = Query(None, ge=0, le=130),
        max_age: Optional[int] = Query(None, ge=0, le=130),
        min_income: Optional[int] = Query(None, ge=0),
        max_income: Optional[int] = Query(None, ge=0),
        min_score: Optional[int] = Query(None, ge=1, le=100),
        max_score: Optional[int] = Query(None, ge=1, le=100),
        search: Optional[str] = Query(None, min_length=1, max_length=64),
        sort_by: str = Query(
            "id",
            pattern="^(id|age|annual_income_k|spending_score|customer_code)$",
        ),
        order: str = Query("asc", pattern="^(asc|desc)$"),
        db: Session = Depends(get_db),
    ):
        if min_age is not None and max_age is not None and min_age > max_age:
            raise HTTPException(status_code=400, detail="min_age cannot exceed max_age")
        if min_income is not None and max_income is not None and min_income > max_income:
            raise HTTPException(
                status_code=400, detail="min_income cannot exceed max_income"
            )
        if min_score is not None and max_score is not None and min_score > max_score:
            raise HTTPException(
                status_code=400, detail="min_score cannot exceed max_score"
            )

        total, items = crud.list_customers(
            db,
            page=page,
            page_size=page_size,
            gender=gender,
            min_age=min_age,
            max_age=max_age,
            min_income=min_income,
            max_income=max_income,
            min_score=min_score,
            max_score=max_score,
            search=search,
            sort_by=sort_by,
            order=order,
        )
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    @app.get(
        "/customers/{customer_id}",
        response_model=schemas.CustomerOut,
        responses={404: {"model": schemas.ErrorOut}},
        tags=["customers"],
    )
    def get_customer(
        customer_id: int = Path(..., ge=1), db: Session = Depends(get_db)
    ):
        obj = crud.get_customer(db, customer_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Customer not found")
        return obj

    @app.post(
        "/customers",
        response_model=schemas.CustomerOut,
        status_code=status.HTTP_201_CREATED,
        responses={409: {"model": schemas.ErrorOut}},
        tags=["customers"],
    )
    def create_customer(
        payload: schemas.CustomerCreate, db: Session = Depends(get_db)
    ):
        if crud.get_customer_by_code(db, payload.customer_code):
            raise HTTPException(
                status_code=409, detail="customer_code already exists"
            )
        try:
            return crud.create_customer(db, payload)
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Could not create customer")

    @app.delete(
        "/customers/{customer_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={404: {"model": schemas.ErrorOut}},
        tags=["customers"],
    )
    def delete_customer(
        customer_id: int = Path(..., ge=1), db: Session = Depends(get_db)
    ):
        if not crud.delete_customer(db, customer_id):
            raise HTTPException(status_code=404, detail="Customer not found")
        return None

    return app


app = create_app()
