from pydantic import BaseModel, ConfigDict, Field, AwareDatetime


class BmiInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    chest_cm: float = Field(gt=0, le=150, allow_inf_nan=False)
    leg_cm: float = Field(gt=0, le=60, allow_inf_nan=False)
    occurred_at: AwareDatetime
