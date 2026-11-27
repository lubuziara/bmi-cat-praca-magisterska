from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class MealInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    day: date
    period: Literal['morning', 'evening']
    food_id: Literal['demo-chicken-can']
    grams: float = Field(gt=0, le=1000, allow_inf_nan=False)
