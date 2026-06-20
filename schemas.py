from pydantic import BaseModel
from typing import Optional
from datetime import date


# ── USER SCHEMAS ─────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ── EXPENSE SCHEMAS ───────────────────────────────────

class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: str
    description: Optional[str] = None
    date: date


class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None


class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: float
    category: str
    description: Optional[str] = None
    receipt_path: Optional[str] = None
    owner_username: str
    date: date

    class Config:
        from_attributes = True