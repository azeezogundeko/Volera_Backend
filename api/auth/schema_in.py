from dataclasses import dataclass
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator
from fastapi import UploadFile, File, Form


@dataclass
class ProfileSchema:
    avatar: Optional[UploadFile] = File(None)
    gender: Optional[Literal["male", "female"]] = Form(None)
    phone: Optional[str] = Form(None)
    address: Optional[str] = Form(None)
    city: Optional[str] = Form(None)
    country: Optional[str] = Form(None)
    interests: List[str] = Form(default=[])  # Updated from `interest` to `interests`
    price_range: Optional[str] = Form(None)  # No alias needed, matches client request
    shopping_frequency: Optional[str] = Form(None)  # No alias needed, matches client request
    preferred_categories: Optional[List[str]] = Form(default=[])  # No alias needed, matches client request
    notification_preferences: Optional[List[str]] = Form(default=[]) # No alias needed, matches client request

# @dataclass
# class PreferencesSchema:
    

class LoginSchema(BaseModel):
    email:str
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    password: str
    # country: str

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
