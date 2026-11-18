import re
from datetime import date as date_type
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from models import CategoryEnum


# ── SHARED VALIDATION RULES ──────────────────────────

def _validate_amount(v: float) -> float:
    if v <= 0:
        raise ValueError("Amount must be greater than 0")
    if v > 10_000_000:
        raise ValueError("Amount is too large")
    return round(v, 2)  # round to 2 decimal places


def _validate_title(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("Title cannot be empty")
    if len(v) > 100:
        raise ValueError("Title must be 100 characters or less")
    return v


def _validate_date(v: date_type) -> date_type:
    if v > date_type.today():
        raise ValueError("Date cannot be in the future")
    return v


# ── USER SCHEMAS ─────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v):
        v = v.strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]{3,30}", v):
            raise ValueError("Username must be 3-30 characters: letters, numbers, '.', '_' or '-'")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v):
        v = v.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("Enter a valid email address")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ── EXPENSE SCHEMAS ───────────────────────────────────

class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: CategoryEnum          # must be one of food/transport/health/entertainment/other
    description: Optional[str] = None
    date: date_type

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        return _validate_amount(v)

    @field_validator("title")
    @classmethod
    def title_cannot_be_empty(cls, v):
        return _validate_title(v)

    @field_validator("date")
    @classmethod
    def date_cannot_be_future(cls, v):
        return _validate_date(v)


class ExpenseUpdate(BaseModel):
    """PATCH body — every field optional, but the same rules apply to any field sent."""
    title: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[CategoryEnum] = None
    description: Optional[str] = None
    date: Optional[date_type] = None

    @field_validator("title", "amount", "category", "date", mode="before")
    @classmethod
    def required_fields_cannot_be_null(cls, v, info):
        # Sending "title": null would otherwise reach the DB and fail NOT NULL
        if v is None:
            raise ValueError(f"{info.field_name} cannot be null")
        return v

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        return _validate_amount(v)

    @field_validator("title")
    @classmethod
    def title_cannot_be_empty(cls, v):
        return _validate_title(v)

    @field_validator("date")
    @classmethod
    def date_cannot_be_future(cls, v):
        return _validate_date(v)


class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: float
    category: CategoryEnum
    description: Optional[str] = None
    receipt_path: Optional[str] = None
    owner_username: str
    date: date_type

    model_config = ConfigDict(from_attributes=True)


class PaginatedExpenseResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[ExpenseResponse]
