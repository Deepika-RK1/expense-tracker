from pydantic import BaseModel, field_validator
from typing import Optional,List
from datetime import date as date_type




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
    
# schemas.py — update ExpenseCreate
from pydantic import BaseModel, field_validator
from datetime import date as date_type

class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: str
    description: Optional[str] = None
    date: date_type

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return round(v, 2)  # round to 2 decimal places

    @field_validator("title")
    @classmethod
    def title_cannot_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("date")
    @classmethod
    def date_cannot_be_future(cls, v):
        if v > date_type.today():
            raise ValueError("Date cannot be in the future")
        return v

class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date_type] = None


class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: float
    category: str
    description: Optional[str] = None
    receipt_path: Optional[str] = None
    owner_username: str
    date: date_type

class PaginatedExpenseResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[ExpenseResponse]


    class Config:
        from_attributes = True