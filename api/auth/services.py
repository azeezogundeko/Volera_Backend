import asyncio
from typing import Optional
from datetime import datetime, timedelta, timezone
import hashlib

from appwrite.client import AppwriteException
from db import user_db

from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from .schema import UserIn, TokenData

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from appwrite.services.users import Users



pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def hash_email(email: str) -> str:
    # Generate a SHA-256 hash and truncate it to 36 characters
    hashed = hashlib.sha256(email.encode()).hexdigest()
    return hashed[:36]

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


async def get_user(email: str) -> Optional[UserIn]:
    try:
        hashed_email = hash_email(email)
        user = await asyncio.to_thread(user_db.get, hashed_email)
        return UserIn(**user)
    except AppwriteException:
        return None
    

async def authenticate_user(email: str, password: str) -> Optional[UserIn]:
    user = await get_user(email)
    if not user or not verify_password(password, user.password):
        return None
    return user


# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserIn:
    try:
        payload = decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        token_data = TokenData(email=email)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await get_user(token_data.email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
