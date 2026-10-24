from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    shop_name: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    merchant_id: int | None = None
    merchant_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str