from typing import Literal
from pydantic import BaseModel


class SendVerificationRequest(BaseModel):
    channel: Literal["email", "phone"]
