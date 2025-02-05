import random
import asyncio
from typing import Any, Optional
from datetime import datetime, timedelta, timezone
import hashlib

from appwrite.client import AppwriteException
from db import user_db
from .model import UserProfile, UserPreferences

from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from .schema import UserIn, TokenData, UserOut
from .schema_in import ProfileSchema, UserCreate

from utils.emails import send_new_user_email

from appwrite.input_file import InputFile
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from appwrite.query import Query



pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def hash_email(email: str) -> str:
    # Generate a SHA-256 hash and truncate it to 36 characters
    hashed = hashlib.sha256(email.encode()).hexdigest()
    return hashed[:36]

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def split_name(full_name: str):
    # Try splitting by underscore
    if '_' in full_name:
        parts = full_name.split('_')
        return parts[0], parts[-1]
    
    # Try splitting by space
    parts = full_name.split()
    if len(parts) > 1:
        return parts[0], parts[-1]
    
    # If no clear split, use the full name as first name
    return full_name, ''



def generate_random_six_digit_number():
    return random.randint(100000, 999999)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

async def get_user_by_email(email: str):
    try:
        kwgs = dict(
            queries = [Query.equal('email', email)]
        )

        users: str | Any | bytes | Nones = await asyncio.to_thread(user_db.list, **kwgs)
        user = users["users"][0]
        return UserIn(**user)
    except Exception:
        return None

async def get_user(email: str) -> Optional[UserIn]:
    try:
        user_id = hash_email(email)
        user = await asyncio.to_thread(user_db.get, user_id)
        
        return UserIn(**user)
    except AppwriteException:
        return None

async def get_user_by_id(user_id) -> Optional[UserIn]:
    try:
        user = await asyncio.to_thread(user_db.get, user_id)
        return UserIn(**user)
    except Exception:
        return None
    

async def authenticate_user(email: str, password: str) -> Optional[UserIn]:
    user = await get_user_by_email(email)
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
    
    user = await get_user_by_email(token_data.email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def create_new_user(payload: UserCreate, background_tasks: BackgroundTasks):
    user = await get_user_by_email(payload.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = get_password_hash(payload.password)
    user_id=hash_email(payload.email)
    p = dict(
        user_id=user_id,
        email=payload.email,
        password=hashed_password,
        name=payload.first_name + "_" + payload.last_name
    )
    response = await asyncio.to_thread(user_db.create_argon2_user, **p)
    await asyncio.to_thread(user_db.update_labels, user_id, ["unsubscribed"])
    validation_code = generate_random_six_digit_number()
    await asyncio.to_thread(user_db.update_prefs, user_id, 
        {
            "validation_code": validation_code, 
            "theme": "black", 
            "notification": True, 
            "credits": 500,
            "timezone": payload.timezone
            })

    background_tasks.add_task(send_new_user_email, validation_code, p["email"])

    first_name, last_name = response["name"].rsplit("_", 1)

    user = dict(
        user_id=response["$id"],
        email=response["email"],
        first_name=first_name,
        last_name=last_name,
        is_pro=False,
        created_at=response["$createdAt"],
        updated_at=response["$updatedAt"]
    )
    
    access_token = create_access_token(data={"sub": p["email"]})
    return  {
        "user": user,
        "token": {"access_token": access_token, "token_type": "bearer"}
        }




async def create_user_profile(
    user: UserIn,
    payload: ProfileSchema, 
    ):
    file_id = None
    if payload.avatar:
        file_id = UserProfile.get_unique_id()
        file = payload.avatar.file
        file.seek(0)
        file = InputFile.from_bytes(
            file.read(),
            payload.avatar.filename,
        )
        await UserProfile.create_file(file_id, file)


    user_profile = await UserProfile.create(
        document_id=user.id,
        data={
            # "user_id": user.id,
            "phone": payload.phone,
            "gender": payload.gender,
            "city": payload.city,
            "country": payload.country,
            "address": payload.address,
            "avatar": file_id
        }
    )
    user_preferences = await UserPreferences.create(
        document_id=user.id,
        data={
            "interest": payload.interests,
            "price_range": payload.price_range,
            "shopping_frequency": payload.shopping_frequency,
            "notification_preferences": payload.notification_preferences,
            # "user_id": user.id
        }
    )

    return {
            "user": user,
            "profile": user_profile.to_dict(),
            "preference": user_preferences.to_dict()
        }
