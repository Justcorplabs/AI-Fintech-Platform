from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


def validate_secure_password(value: str) -> str:
    if value != value.strip():
        raise ValueError(
            "Password cannot begin or end with whitespace."
        )

    requirements = {
        "an uppercase letter": any(
            character.isupper()
            for character in value
        ),
        "a lowercase letter": any(
            character.islower()
            for character in value
        ),
        "a number": any(
            character.isdigit()
            for character in value
        ),
    }

    missing = [
        requirement
        for requirement, passed in requirements.items()
        if not passed
    ]

    if missing:
        raise ValueError(
            "Password must contain "
            + ", ".join(missing)
            + "."
        )

    return value


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    organisation: str | None = Field(
        default=None,
        max_length=150,
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return str(value).strip().lower()

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())

        if len(cleaned) < 2:
            raise ValueError(
                "Full name must contain at least 2 characters."
            )

        return cleaned

    @field_validator("organisation")
    @classmethod
    def normalise_organisation(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())
        return cleaned or None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_secure_password(value)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return str(value).strip().lower()


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return str(value).strip().lower()


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: str | None = None
    reset_url: str | None = None
    expires_in: int | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=32, max_length=500)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validate_secure_password(value)

    @model_validator(mode="after")
    def validate_password_confirmation(self):
        if self.new_password != self.confirm_password:
            raise ValueError(
                "New password and confirmation do not match."
            )

        return self


class PasswordResetResponse(BaseModel):
    message: str
    revoked_sessions: int


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class LogoutAllResponse(BaseModel):
    message: str
    revoked_sessions: int


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    organisation: str | None = None

    model_config = ConfigDict(from_attributes=True)