from typing import Annotated
from pydantic import BaseModel, BeforeValidator, EmailStr
from app.validation.normalize_email import normalize_email


class ForgotRequest(BaseModel):
    email: Annotated[EmailStr, BeforeValidator(normalize_email)]
