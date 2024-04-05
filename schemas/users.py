from pydantic import BaseModel, EmailStr, Field


class AuthUserBase(BaseModel):
    username: str
    password: str


class UserBase(BaseModel):
    firstname: str
    surname: str
    email: EmailStr | None = Field(default=None)
    password: str
    phone_number: str
    street_address: str
    active: bool

