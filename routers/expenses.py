import os
import uuid
import time
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, HTTPException, File, UploadFile, status, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Expense, CategoryEnum
from schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse,PaginatedExpenseResponse
from auth import get_current_user
from exceptions import ResourceNotFoundException

router = APIRouter(
    prefix="/expenses",
    tags=["Expenses"]
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_RECEIPT_BYTES = 5 * 1024 * 1024


def detect_image_type(contents: bytes) -> Optional[str]:
    """Return 'jpg' or 'png' from the file's magic bytes, else None"""
    if contents.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    return None


def remove_file(path: Optional[str]) -> None:
    """Delete a stored receipt file if it exists"""
    if path and os.path.isfile(path):
        try:
            os.remove(path)
        except OSError as e:
            print(f"⚠️ Could not delete {path}: {e}")


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

@router.get("/", response_model=PaginatedExpenseResponse)
def get_all_expenses(
    page: int = Query(1, ge=1, description="Page number, starting at 1"),
    limit: int = Query(10, ge=1, le=100, description="Items per page (1-100)"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    query = (
        db.query(Expense)
        .filter(Expense.owner_username == current_user)
        .order_by(Expense.date.desc(), Expense.id.desc())   # stable order across pages
    )
    total = query.count()
    expenses = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": expenses
    }


# ── FILTER ────────────────────────────────────────────

@router.get("/filter", response_model=List[ExpenseResponse])
def filter_expenses(
    category: Optional[CategoryEnum] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date cannot be after to_date"
        )

    query = db.query(Expense).filter(Expense.owner_username == current_user)

    if category:
        query = query.filter(Expense.category == category)
    if from_date:
        query = query.filter(Expense.date >= from_date)
    if to_date:
        query = query.filter(Expense.date <= to_date)

    return query.order_by(Expense.date.desc(), Expense.id.desc()).all()


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

    receipt_path = expense.receipt_path
    db.delete(expense)
    db.commit()
    remove_file(receipt_path)   # don't leave orphaned receipt images on disk
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

    if len(contents) > MAX_RECEIPT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 5MB."
        )

    # The content type comes from the client, so also check the real bytes,
    # and take the extension from them instead of the user's filename
    extension = detect_image_type(contents)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not a valid JPEG or PNG image."
        )

    unique_name = f"{uuid.uuid4()}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(contents)

    old_receipt = expense.receipt_path
    expense.receipt_path = file_path
    db.commit()
    db.refresh(expense)
    if old_receipt and old_receipt != file_path:
        remove_file(old_receipt)   # replacing a receipt removes the old image

    return {
        "message": "Receipt uploaded successfully",
        "expense_id": expense.id,
        "saved_as": unique_name,
        "size_bytes": len(contents),
        "content_type": file.content_type
    }