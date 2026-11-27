from pydantic import BaseModel, Field


class SetupConfirmRequest(BaseModel):
    setup_challenge: str = Field(min_length=32, max_length=128)
    code: str = Field(min_length=6, max_length=6)


class MfaVerifyRequest(BaseModel):
    mfa_challenge: str = Field(min_length=32, max_length=128)
    code: str = Field(min_length=6, max_length=128)


class MfaReauthRequest(BaseModel):
    password: str | None = Field(default=None, max_length=128)
    google_id_token: str | None = Field(default=None, max_length=4096)
    code: str | None = Field(default=None, min_length=6, max_length=128)
