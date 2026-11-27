from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime


class EventInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str = Field(min_length=2, max_length=120)
    kind: Literal['vet', 'medication']
    occurred_at: AwareDatetime
    note: str = Field(default='', max_length=2000)
