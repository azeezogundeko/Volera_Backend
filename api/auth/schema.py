from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator


class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    hashed_password: str


class HashOptions(BaseModel):
    type: str
    memoryCost: Optional[int] =  None
    timeCost: Optional[int] = None
    threads: Optional[int] =  None

class Target(BaseModel):
    id: str = Field(alias="$id")
    created_at: datetime = Field(alias="$createdAt")
    updated_at: datetime = Field(alias="$updatedAt")
    name: Optional[str] = ''
    userId: str
    providerId: Optional[str] = None
    providerType: str
    identifier: str
    expired: bool

class UserIn(BaseModel):
    id: str = Field(alias="$id")
    created_at: datetime = Field(alias="$createdAt")
    updated_at: datetime = Field(alias="$updatedAt")
    name: str
    hash: str
    hashOptions: HashOptions
    registration: datetime
    status: bool
    labels: List[str]
    passwordUpdate: datetime
    phone: Optional[str] = ''
    password: str
    emailVerification: bool
    phoneVerification: bool
    mfa: bool
    email: str
    prefs: Dict[str, str]
    targets: List[Target]
    accessedAt: Optional[str] = ''

    class Config:
        # Exclude confidential fields like 'password' and 'email' when converting to dict
        exclude = {"passwordUpdate" ,"hashOptions", "hash", "hashOptions", "mfa", }

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str

    @field_validator('password')
    def password_strength(cls, v: str):
        # Ensure password is at least 8 characters long
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Optionally, add more checks (e.g., for uppercase letters, numbers, etc.)
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        return v

class UserOut(BaseModel):
    user_id: str
    created_at: datetime 
    updated_at: datetime 
    first_name: str
    last_name: str
    email:str
    

class Token(BaseModel):
    access_token: str
    token_type: str

class UserPublic(BaseModel):
    token: Token
    user: UserOut


class TokenData(BaseModel):
    email: Optional[str] = None

class LoginSchema(BaseModel):
    email:str
    password: str