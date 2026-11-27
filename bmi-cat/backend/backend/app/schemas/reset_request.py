from pydantic import BaseModel, Field


class ResetRequest(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    password: str = Field(min_length=12, max_length=128)
