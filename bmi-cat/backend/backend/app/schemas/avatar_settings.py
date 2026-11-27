from typing import Literal
from pydantic import BaseModel, ConfigDict


class AvatarSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1] = 1
    fur: Literal["hairless", "short", "long", "extra_long"] = "short"
    coat: Literal["white", "black", "ginger", "tabby", "tricolor", "ginger_white", "ginger_black_white", "purple", "yellow", "red"] = "white"
    eyes: Literal["green", "amber", "blue", "brown", "gray", "heterochromia", "purple", "pink", "turquoise", "red"] = "green"
    size: Literal["kitten", "adult"] = "adult"
    body: Literal["emaciated", "slim", "medium", "large", "xxl"] = "medium"
