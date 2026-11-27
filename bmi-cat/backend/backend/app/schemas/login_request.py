from typing import Annotated
from pydantic import BaseModel, BeforeValidator, EmailStr, Field
from app.validation.normalize_email import normalize_email


class LoginRequest(BaseModel):
    email: Annotated[EmailStr, BeforeValidator(normalize_email)]
    password: str = Field(min_length=1, max_length=128)
