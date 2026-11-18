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
- ✅ Input validation (amount, title, date, category) on create, PUT and PATCH
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
- Category must be one of the allowed values (an invalid category used to crash the API with a 500)
- The same rules apply to PATCH, and required fields can't be set to null
- `page` ≥ 1 and `limit` between 1 and 100

### 4. Bug fixes and hardening
- Registering with an existing email returns a clear 400 instead of a 500
- Receipt uploads check the file's real bytes (JPEG/PNG), not just the client's content type
- Replacing or deleting an expense removes its old receipt image from disk
- Expenses are returned newest first, so pagination is stable
- `from_date` after `to_date` returns a 400; monthly report validates the year
- JWT secret key read from the `SECRET_KEY` environment variable instead of being hardcoded

### 5. Automated tests
17 pytest tests covering auth, validation, CRUD, pagination, filters, summaries, user isolation and receipt uploads.

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
| pytest | Automated API tests |
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
├── tests/            ← pytest test suite
├── uploads/          ← receipt images stored here
└── routers/
    ├── auth.py       ← POST /users/register, POST /users/login
    ├── expenses.py   ← full CRUD + receipt upload + pagination
    └── summary.py    ← category summary + monthly report


---

## 🚀 Getting Started

### 1. Clone the repo
bash
git clone https://github.com/Deepika-RK1/expense-tracker.git
cd expense-tracker


### 2. Create virtual environment
bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows


### 3. Install dependencies
bash
pip install -r requirements.txt


### 4. Set a secret key and run the server
bash
export SECRET_KEY="any-long-random-string"   # Windows: set SECRET_KEY=any-long-random-string
uvicorn main:app --reload


### 5. Open API docs

http://localhost:8000/docs

### 6. Run the tests
bash
pip install pytest httpx
pytest -q


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
| page / limit | page ≥ 1, limit 1–100 |
| category | Must be one of: food, transport, health, entertainment, other |
| Receipt file | Must really be a JPEG or PNG (checked by file bytes), max 5MB |

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
