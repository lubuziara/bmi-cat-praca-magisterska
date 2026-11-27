from typing import Literal
from pydantic import BaseModel, Field


class VerificationRequest(BaseModel):
    channel: Literal["email", "phone"]
    code: str = Field(pattern=r"^[0-9]{6}$")
