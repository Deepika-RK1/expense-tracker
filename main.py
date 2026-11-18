import time
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import auth, expenses, summary
from exceptions import ResourceNotFoundException, DuplicateResourceException

Base.metadata.create_all(bind=engine)

logger = logging.getLogger("expense_tracker")

app = FastAPI(
    title="Expense Tracker API",
    description="A production-grade expense tracking REST API built with FastAPI.",
    version="1.0.0"
)


# ── CORS ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # auth uses a Bearer header, not cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REQUEST LOGGING MIDDLEWARE ─────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    print(f"\n→ {request.method} {request.url}")

    response = await call_next(request)

    duration = time.time() - start_time
    print(f"← {response.status_code} in {duration:.3f}s")
    response.headers["X-Process-Time"] = str(duration)
    return response


# ── EXCEPTION HANDLERS ─────────────────────────────────
@app.exception_handler(ResourceNotFoundException)
async def not_found_handler(request: Request, exc: ResourceNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Not Found",
            "message": f"{exc.resource} with id {exc.id} not found"
        }
    )


@app.exception_handler(DuplicateResourceException)
async def duplicate_handler(request: Request, exc: DuplicateResourceException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Duplicate Resource",
            "message": exc.message
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " → ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"].replace("Value error, ", "")
        })

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": errors
        }
    )

@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "Something went wrong on our end"
        }
    )


# ── ROUTERS ───────────────────────────────────────────
app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(summary.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Expense Tracker API is running", "docs": "/docs"}
