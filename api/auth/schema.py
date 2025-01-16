from typing import Any, List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class BaseSchema(BaseModel):
    message: str
    error: Optional[str] = None

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
    prefs: Dict[str, Any]
    targets: List[Target]
    accessedAt: Optional[str] = ''


class UserOut(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime 
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: str
    email:str
    is_pro: bool
    profile_image: Optional[Any]

    @field_validator("name", mode="after")
    def get_name_splits(cls, v):
        first_name, last_name = v.rsplit("_", 1)
        return first_name, last_name

class UserProfileSchemaOut(BaseModel):

    gender: str
    phone: str
    address: str
    city: str
    country: str

class UserPreferenceSchemaOut(BaseModel):
    interest: Optional[List[str]] = []
    price_range: Optional[str] = None
    shopping_frequency: Optional[str] = None
    preferred_categories: Optional[List[str]] = []
    notification_prefrences: Optional[List[str]] = []


class UserProfileData(BaseModel):
    user: UserOut
    preference: UserPreferenceSchemaOut #preference
    profile: UserProfileSchemaOut


class UserProfileOut(BaseSchema):
    data: UserProfileData


class Token(BaseModel):
    access_token: str
    token_type: str

class UserPublic(BaseModel):
    token: Token
    user: UserOut


class TokenData(BaseModel):
    email: Optional[str] = None

