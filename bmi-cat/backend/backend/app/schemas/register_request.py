from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, AfterValidator, BeforeValidator, EmailStr, Field, field_validator
from app.validation.normalize_email import normalize_email
from app.validation.validate_name import validate_name
from app.validation.validate_phone import validate_phone
from app.schemas.cat_request import CatRequest


class RegisterRequest(BaseModel):
    first_name: Annotated[str, AfterValidator(validate_name)]
    last_name: Annotated[str, AfterValidator(validate_name)]
    gender: Literal["female", "male", "other", "undisclosed"]
    birth_date: date
    phone: Annotated[str, AfterValidator(validate_phone)]
    email: Annotated[EmailStr, BeforeValidator(normalize_email)]
    password: str = Field(min_length=12, max_length=128)
    cat: CatRequest

    @field_validator("birth_date")
    @classmethod
    def check_birth_date(cls, value):
        today = date.today()
        if not date(today.year - 120, 1, 1) <= value <= today:
            raise ValueError("Podaj poprawną datę urodzenia.")
        return value
