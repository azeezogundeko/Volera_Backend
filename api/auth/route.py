import asyncio
from . import services
from .schema import UserCreate, User, LoginSchema, UserIn, UserPublic, UserOut
from db import user_db

from fastapi import Depends, HTTPException, APIRouter


router = APIRouter()


@router.post("/auth/register", response_model=UserPublic)
async def register_user(payload: UserCreate):
    user = await services.get_user(payload.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = services.get_password_hash(payload.password)
    payload = dict(
        user_id=services.hash_email(payload.email),
        email=payload.email,
        password=hashed_password,
        name=payload.first_name + "_" + payload.last_name
    )
    response = await asyncio.to_thread(user_db.create_argon2_user, **payload)

    first_name, last_name = response["name"].rsplit("_", 1)
    user = UserOut(
        user_id=response["$id"],
        email=response["email"],
        first_name=first_name,
        last_name=last_name,
        created_at=response["$createdAt"],
        updated_at=response["$updatedAt"]
    )
    
    access_token = services.create_access_token(data={"sub": payload["email"]})
    return  {
        "user": user,
        "token": {"access_token": access_token, "token_type": "bearer"}
        }

@router.post("/auth/login", response_model=UserPublic)
async def login(payload: LoginSchema):
    user = await services.authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = services.create_access_token(data={"sub": payload.email})
    first_name, last_name = user.name.rsplit("_", 1)
    user = UserOut(
        user_id=user.id,
        email=user.email,
        first_name=first_name,
        last_name=last_name,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
    return  {
        "user": user,
        "token": {"access_token": access_token, "token_type": "bearer"}
        }

@router.get("/auth/me", response_model=User)
async def get_me(current_user: UserIn = Depends(services.get_current_user)):
    return current_user