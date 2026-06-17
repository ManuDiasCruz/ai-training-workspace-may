from typing import Optional, Tuple, List

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from . import models, schemas


def get_customer(db: Session, customer_id: int) -> Optional[models.Customer]:
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()


def get_customer_by_code(db: Session, code: str) -> Optional[models.Customer]:
    return (
        db.query(models.Customer)
        .filter(models.Customer.customer_code == code)
        .first()
    )


def list_customers(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    gender: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_income: Optional[int] = None,
    max_income: Optional[int] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: str = "id",
    order: str = "asc",
) -> Tuple[int, List[models.Customer]]:
    q = db.query(models.Customer)

    if gender:
        q = q.filter(models.Customer.gender == gender)
    if min_age is not None:
        q = q.filter(models.Customer.age >= min_age)
    if max_age is not None:
        q = q.filter(models.Customer.age <= max_age)
    if min_income is not None:
        q = q.filter(models.Customer.annual_income_k >= min_income)
    if max_income is not None:
        q = q.filter(models.Customer.annual_income_k <= max_income)
    if min_score is not None:
        q = q.filter(models.Customer.spending_score >= min_score)
    if max_score is not None:
        q = q.filter(models.Customer.spending_score <= max_score)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            or_(
                models.Customer.customer_code.ilike(pattern),
                models.Customer.gender.ilike(pattern),
            )
        )

    sortable = {
        "id": models.Customer.id,
        "age": models.Customer.age,
        "annual_income_k": models.Customer.annual_income_k,
        "spending_score": models.Customer.spending_score,
        "customer_code": models.Customer.customer_code,
    }
    sort_col = sortable.get(sort_by, models.Customer.id)
    if order.lower() == "desc":
        sort_col = sort_col.desc()
    # Every sort includes the unique primary key as a tiebreaker so that a
    # record cannot move between pages when several customers share a value.
    q = q.order_by(sort_col, models.Customer.id)

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return total, items


def create_customer(db: Session, payload: schemas.CustomerCreate) -> models.Customer:
    obj = models.Customer(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_customer(db: Session, customer_id: int) -> bool:
    obj = get_customer(db, customer_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def stats(db: Session) -> dict:
    total = db.query(func.count(models.Customer.id)).scalar() or 0
    by_gender_rows = (
        db.query(models.Customer.gender, func.count(models.Customer.id))
        .group_by(models.Customer.gender)
        .all()
    )
    by_gender = {g: c for g, c in by_gender_rows}
    avg_age = db.query(func.avg(models.Customer.age)).scalar() or 0
    avg_income = db.query(func.avg(models.Customer.annual_income_k)).scalar() or 0
    avg_score = db.query(func.avg(models.Customer.spending_score)).scalar() or 0
    return {
        "total_customers": total,
        "by_gender": by_gender,
        "avg_age": round(float(avg_age), 2),
        "avg_annual_income_k": round(float(avg_income), 2),
        "avg_spending_score": round(float(avg_score), 2),
    }
