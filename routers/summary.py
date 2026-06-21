from typing import List, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import Expense
from schemas import ExpenseResponse
from auth import get_current_user

router = APIRouter(
    prefix="/summary",
    tags=["Summary"]
)


@router.get("/by-category", response_model=Dict[str, float])
def summary_by_category(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    results = (
        db.query(Expense.category, func.sum(Expense.amount))
        .filter(Expense.owner_username == current_user)
        .group_by(Expense.category)
        .all()
    )
    return {category: round(total, 2) for category, total in results}


@router.get("/total")
def summary_total(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    total = (
        db.query(func.sum(Expense.amount))
        .filter(Expense.owner_username == current_user)
        .scalar()
    )
    return {"total_spent": round(total or 0.0, 2)}


@router.get("/recent", response_model=List[ExpenseResponse])
def summary_recent(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    return (
        db.query(Expense)
        .filter(Expense.owner_username == current_user)
        .order_by(Expense.date.desc())
        .limit(5)
        .all()
    )

# routers/summary.py — add this endpoint
from sqlalchemy import extract

@router.get("/monthly")
def monthly_report(
    year: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    results = (
        db.query(
            extract("month", Expense.date).label("month"),
            func.sum(Expense.amount).label("total")
        )
        .filter(
            Expense.owner_username == current_user,
            extract("year", Expense.date) == year
        )
        .group_by(extract("month", Expense.date))
        .all()
    )

    month_names = {
        1: "January", 2: "February", 3: "March",
        4: "April", 5: "May", 6: "June",
        7: "July", 8: "August", 9: "September",
        10: "October", 11: "November", 12: "December"
    }

    breakdown = {
        month_names[int(month)]: round(total, 2)
        for month, total in results
    }

    if not breakdown:
        return {"year": year, "monthly_breakdown": {}, "total_for_year": 0.0}

    highest = max(breakdown, key=breakdown.get)
    total_for_year = round(sum(breakdown.values()), 2)

    return {
        "year": year,
        "monthly_breakdown": breakdown,
        "highest_spending_month": highest,
        "total_for_year": total_for_year
    }