from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, AfterValidator, Field, model_validator
from app.validation.validate_name import validate_name
from app.schemas.avatar_settings import AvatarSettings


class CatRequest(BaseModel):
    name: Annotated[str, AfterValidator(validate_name)]
    gender: Literal["female", "male", "unknown"]
    birth_date: date | None = None
    estimated_age_months: int | None = Field(default=None, ge=0, le=480, strict=True)
    avatar: AvatarSettings = Field(default_factory=AvatarSettings)

    @model_validator(mode="after")
    def check_age(self):
        if (self.birth_date is None) == (self.estimated_age_months is None):
            raise ValueError("Podaj datę urodzenia albo przybliżony wiek kota.")
        if self.birth_date and not date(date.today().year - 40, 1, 1) <= self.birth_date <= date.today():
            raise ValueError("Data urodzenia kota nie może być przyszła ani starsza niż 40 lat.")
        return self
