# auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# ── CONFIG ──────────────────────────────────────────
SECRET_KEY = "your-secret-key-keep-this-safe"  # in production use a long random string
ALGORITHM = "HS256"           # signing algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ── PASSWORD HASHING ─────────────────────────────────
# bcrypt is the industry standard for hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── TOKEN EXTRACTION ─────────────────────────────────
# This tells FastAPI: "look for token at /login endpoint"
# Also adds the Authorize button in /docs
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")


# ── FUNCTIONS ────────────────────────────────────────

def hash_password(password: str) -> str:
    """Convert plain password to hashed version"""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Check if plain password matches the hash"""
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    """Create a JWT token with expiry"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})  # add expiry to payload
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> str:
    """Verify token and extract username"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # "sub" = subject = who this token is for
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency — extracts and validates token from request header"""
    return verify_token(token)