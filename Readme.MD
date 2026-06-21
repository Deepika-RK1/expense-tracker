# 💰 Expense Tracker API

A production-grade REST API for tracking personal expenses, built with *FastAPI* and *SQLAlchemy*.

> This project is a fork of [Anand-1216/expense-tracker](https://github.com/Anand-1216/expense-tracker).
> I extended it with pagination, monthly analytics, and input validation.

---

## ✨ Features

- 🔐 JWT Authentication (register & login)
- 💸 Full CRUD for expenses
- 🧾 Receipt image upload (JPEG/PNG, max 5MB)
- 🔍 Filter expenses by category and date range
- 📄 Pagination on expenses list
- 📊 Spending summary by category
- 📅 Monthly spending report with highest spending month
- ✅ Input validation (amount, title, date)
- ⚡ Background task logging
- 🌐 CORS middleware
- 📋 Request logging with response time headers
- 🛡️ Global error handling with clean JSON responses
- 👤 Complete user data isolation

---

## 🆕 My Enhancements

### 1. Pagination
Added page and limit query parameters to GET /expenses/ so large datasets don't get fetched all at once.


GET /expenses/?page=1&limit=10   → first 10 expenses
GET /expenses/?page=2&limit=10   → next 10 expenses


Response includes total count, current page, and limit alongside the data.

### 2. Monthly Spending Report
New endpoint GET /summary/monthly?year=2026 that breaks down spending month by month and identifies the highest spending month.

json
{
  "year": 2026,
  "monthly_breakdown": {
    "January": 2500.0,
    "June": 3200.0
  },
  "highest_spending_month": "June",
  "total_for_year": 5700.0
}


### 3. Input Validation
Added Pydantic field validators to enforce business rules before data hits the database:
- Amount must be greater than 0
- Title cannot be empty or blank
- Date cannot be in the future

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| FastAPI | Web framework |
| SQLAlchemy | ORM |
| SQLite | Database |
| python-jose | JWT tokens |
| passlib + bcrypt | Password hashing |
| Pydantic v2 | Data validation + field validators |
| Uvicorn | ASGI server |

---

## 📁 Project Structure


expense-tracker/
├── main.py           ← app entry point, middleware, error handlers
├── database.py       ← DB connection and session
├── models.py         ← SQLAlchemy table definitions
├── schemas.py        ← Pydantic request/response models + validators
├── auth.py           ← JWT logic, password hashing
├── exceptions.py     ← custom exception classes
├── uploads/          ← receipt images stored here
└── routers/
    ├── auth.py       ← POST /users/register, POST /users/login
    ├── expenses.py   ← full CRUD + receipt upload + pagination
    └── summary.py    ← category summary + monthly report


---

## 🚀 Getting Started

### 1. Clone the repo
bash
git clone https://github.com/Deepika-XXXX/expense-tracker.git
cd expense-tracker


### 2. Create virtual environment
bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows


### 3. Install dependencies
bash
pip install -r requirements.txt


### 4. Run the server
bash
uvicorn main:app --reload


### 5. Open API docs

http://localhost:8000/docs


---

## 🔗 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /users/register | Register a new user |
| POST | /users/login | Login and get JWT token |

### Expenses
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /expenses/ | Create an expense |
| GET | /expenses/?page=1&limit=10 | Get paginated expenses |
| GET | /expenses/filter | Filter by category/date range |
| GET | /expenses/{id} | Get one expense |
| PUT | /expenses/{id} | Full update |
| PATCH | /expenses/{id} | Partial update |
| DELETE | /expenses/{id} | Delete expense |
| POST | /expenses/{id}/receipt | Upload receipt image |

### Summary
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /summary/by-category | Total spent per category |
| GET | /summary/total | Grand total |
| GET | /summary/recent | Last 5 expenses |
| GET | /summary/monthly?year=2026 | Monthly breakdown with highest month |

---

## ✅ Input Validation Rules

| Field | Rule |
|-------|------|
| amount | Must be greater than 0 |
| title | Cannot be empty or blank |
| date | Cannot be in the future |
| category | Must be one of: food, transport, health, entertainment, other |
| Receipt file | Must be JPEG or PNG, max 5MB |

---

## 🧪 Quick Test Flow


1. POST /users/register      → create account
2. POST /users/login         → get token
3. Authorize in Swagger UI
4. POST /expenses/           → add expenses
5. GET  /expenses/?page=1    → see paginated results
6. GET  /summary/monthly?year=2026  → see monthly breakdown
7. Try amount: -100          → see validation error


---

## 📌 Notes

- All expense endpoints require JWT authentication
- Users can only access their own expenses
- Receipts must be JPEG or PNG, max 5MB
- Pagination defaults: page=1, limit=10