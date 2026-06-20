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