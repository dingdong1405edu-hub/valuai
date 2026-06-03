import os
import secrets
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=_ALGORITHM)


def create_user_token(uid: int, email: str) -> str:
    payload = {
        "sub": str(uid),
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=30),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[_ALGORITHM])


def decode_user_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[_ALGORITHM])
