# 💰 Expense Tracker API

A production-grade REST API for tracking personal expenses, built with **FastAPI** and **SQLAlchemy**.

---

## ✨ Features

- 🔐 JWT Authentication (register & login)
- 💸 Full CRUD for expenses
- 🧾 Receipt image upload (JPEG/PNG)
- 🔍 Filter expenses by category and date range
- 📊 Spending summary by category
- ⚡ Background task logging
- 🌐 CORS middleware
- 📋 Request logging with response time headers
- 🛡️ Global error handling with clean JSON responses
- 👤 Complete user data isolation

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| FastAPI | Web framework |
| SQLAlchemy | ORM |
| SQLite | Database |
| python-jose | JWT tokens |
| passlib + bcrypt | Password hashing |
| Pydantic v2 | Data validation |
| Uvicorn | ASGI server |

---

## 📁 Project Structure

```
expense-tracker/
├── main.py           ← app entry point, middleware, error handlers
├── database.py       ← DB connection and session
├── models.py         ← SQLAlchemy table definitions
├── schemas.py        ← Pydantic request/response models
├── auth.py           ← JWT logic, password hashing
├── exceptions.py     ← custom exception classes
├── uploads/          ← receipt images stored here
└── routers/
    ├── auth.py       ← POST /users/register, POST /users/login
    ├── expenses.py   ← full CRUD + receipt upload
    └── summary.py    ← spending analytics
```

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/expense-tracker.git
cd expense-tracker
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install fastapi uvicorn sqlalchemy python-jose[cryptography] passlib[bcrypt] python-multipart
```

### 4. Run the server
```bash
uvicorn main:app --reload
```

### 5. Open API docs
```
http://localhost:8000/docs
```

---

## 🔗 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/register` | Register a new user |
| POST | `/users/login` | Login and get JWT token |

### Expenses
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/expenses/` | Create an expense |
| GET | `/expenses/` | Get all my expenses |
| GET | `/expenses/filter` | Filter by category/date |
| GET | `/expenses/{id}` | Get one expense |
| PUT | `/expenses/{id}` | Full update |
| PATCH | `/expenses/{id}` | Partial update |
| DELETE | `/expenses/{id}` | Delete expense |
| POST | `/expenses/{id}/receipt` | Upload receipt image |

### Summary
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/summary/by-category` | Total spent per category |
| GET | `/summary/total` | Grand total |
| GET | `/summary/recent` | Last 5 expenses |

---

## 🧪 Quick Test Flow

```
1. POST /users/register   → create account
2. POST /users/login      → get token
3. Authorize in Swagger UI
4. POST /expenses/        → add expenses
5. GET  /summary/by-category → see breakdown
```

---

## 📌 Notes

- All expense endpoints require JWT authentication
- Users can only access their own expenses
- Receipts must be JPEG or PNG, max 5MB
- Category must be one of: food, transport, health, entertainment, other