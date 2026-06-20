import enum
from sqlalchemy import Column, Integer, String, Float, Enum, Date, ForeignKey
from database import Base


class CategoryEnum(str, enum.Enum):
    food = "food"
    transport = "transport"
    health = "health"
    entertainment = "entertainment"
    other = "other"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(Enum(CategoryEnum), nullable=False)
    description = Column(String, nullable=True)
    receipt_path = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    owner_username = Column(String, ForeignKey("users.username"), nullable=False)