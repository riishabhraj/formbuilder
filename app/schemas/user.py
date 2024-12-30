from pydantic import BaseModel, EmailStr
from typing import Dict

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    user: User
    message: str = "User registered successfully" 