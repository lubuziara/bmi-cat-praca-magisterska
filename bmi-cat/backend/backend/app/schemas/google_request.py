from pydantic import BaseModel, Field


class GoogleRequest(BaseModel):
    id_token: str = Field(min_length=1, max_length=8192)
