import os
import uuid
import time
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, HTTPException, File, UploadFile, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from models import Expense
from schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from auth import get_current_user
from exceptions import ResourceNotFoundException

router = APIRouter(
    prefix="/expenses",
    tags=["Expenses"]
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── BACKGROUND TASK ───────────────────────────────────

def log_expense_created(title: str, owner_username: str):
    time.sleep(1)
    print(f"📝 Expense '{title}' created by {owner_username}")


# ── CREATE ────────────────────────────────────────────

@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    new_expense = Expense(
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        description=expense.description,
        date=expense.date,
        owner_username=current_user
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    background_tasks.add_task(log_expense_created, new_expense.title, current_user)
    return new_expense


# ── READ ALL ──────────────────────────────────────────

@router.get("/", response_model=List[ExpenseResponse])
def get_all_expenses(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    return db.query(Expense).filter(Expense.owner_username == current_user).all()


# ── FILTER ────────────────────────────────────────────

@router.get("/filter", response_model=List[ExpenseResponse])
def filter_expenses(
    category: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    query = db.query(Expense).filter(Expense.owner_username == current_user)

    if category:
        query = query.filter(Expense.category == category)
    if from_date:
        query = query.filter(Expense.date >= from_date)
    if to_date:
        query = query.filter(Expense.date <= to_date)

    return query.all()


# ── READ ONE ──────────────────────────────────────────

@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.owner_username == current_user
    ).first()

    if not expense:
        raise ResourceNotFoundException(resource="Expense", id=expense_id)
    return expense


# ── FULL UPDATE ───────────────────────────────────────

@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.owner_username == current_user
    ).first()

    if not expense:
        raise ResourceNotFoundException(resource="Expense", id=expense_id)

    expense.title = expense_data.title
    expense.amount = expense_data.amount
    expense.category = expense_data.category
    expense.description = expense_data.description
    expense.date = expense_data.date

    db.commit()
    db.refresh(expense)
    return expense


# ── PARTIAL UPDATE ────────────────────────────────────

@router.patch("/{expense_id}", response_model=ExpenseResponse)
def partial_update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.owner_username == current_user
    ).first()

    if not expense:
        raise ResourceNotFoundException(resource="Expense", id=expense_id)

    update_data = expense_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)
    return expense


# ── DELETE ────────────────────────────────────────────

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.owner_username == current_user
    ).first()

    if not expense:
        raise ResourceNotFoundException(resource="Expense", id=expense_id)

    db.delete(expense)
    db.commit()
    return None


# ── RECEIPT UPLOAD ────────────────────────────────────

@router.post("/{expense_id}/receipt", status_code=status.HTTP_200_OK)
async def upload_receipt(
    expense_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.owner_username == current_user
    ).first()

    if not expense:
        raise ResourceNotFoundException(resource="Expense", id=expense_id)

    allowed_types = ["image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' not allowed. Only JPEG and PNG accepted."
        )

    contents = await file.read()

    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 5MB."
        )

    extension = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(contents)

    expense.receipt_path = file_path
    db.commit()
    db.refresh(expense)

    return {
        "message": "Receipt uploaded successfully",
        "expense_id": expense.id,
        "saved_as": unique_name,
        "size_bytes": len(contents),
        "content_type": file.content_type
    }