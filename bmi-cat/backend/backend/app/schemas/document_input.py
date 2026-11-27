from pydantic import BaseModel, ConfigDict, Field, AwareDatetime


class DocumentInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str = Field(min_length=2, max_length=120)
    image_base64: str = Field(min_length=16, max_length=11200000)
    occurred_at: AwareDatetime
