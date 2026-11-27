from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, AfterValidator
from app.validation.validate_name import validate_name


class PreferenceInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    first_name: Annotated[str, AfterValidator(validate_name)]
    last_name: Annotated[str, AfterValidator(validate_name)]
    cat_name: Annotated[str, AfterValidator(validate_name)]
    notifications: bool = Field(strict=True)
    target_kcal: float = Field(gt=0, le=2000, allow_inf_nan=False)
