import json
from typing import List

from pydantic import (
    field_validator,
    model_validator,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    APP_NAME: str = (
        "AI Fintech Intelligence Platform"
    )

    APP_VERSION: str = "0.1.0"

    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str = (
        "postgresql://postgres:password@localhost:5432/"
        "ai_fintech_db"
    )

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    FAILED_LOGIN_MAX_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15

    FRONTEND_URL: str = "http://localhost:5173"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
    ]

    ENABLE_API_DOCS: bool = True
    CREATE_DATABASE_TABLES: bool = True

    DATABASE_POOL_PRE_PING: bool = True
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_RECYCLE_SECONDS: int = 300

    # File-upload and CV-processing limits
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_CV_PAGES: int = 100
    MAX_CV_TEXT_CHARACTERS: int = 500_000
    MAX_DOCX_UNCOMPRESSED_MB: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator(
        "ENVIRONMENT",
        mode="before",
    )
    @classmethod
    def normalise_environment(
        cls,
        value: str,
    ) -> str:
        environment = str(
            value or "development"
        ).strip().lower()

        allowed = {
            "development",
            "testing",
            "staging",
            "production",
        }

        if environment not in allowed:
            raise ValueError(
                "ENVIRONMENT must be development, "
                "testing, staging, or production."
            )

        return environment

    @field_validator(
        "ALLOWED_ORIGINS",
        mode="before",
    )
    @classmethod
    def parse_allowed_origins(
        cls,
        value,
    ):
        if value is None:
            return [
                "http://localhost:5173",
            ]

        if isinstance(
            value,
            list,
        ):
            return [
                str(origin).strip().rstrip("/")
                for origin in value
                if str(origin).strip()
            ]

        if isinstance(
            value,
            str,
        ):
            raw_value = value.strip()

            if not raw_value:
                return []

            if raw_value.startswith("["):
                try:
                    parsed = json.loads(
                        raw_value
                    )

                    if not isinstance(
                        parsed,
                        list,
                    ):
                        raise ValueError

                    return [
                        str(origin).strip().rstrip("/")
                        for origin in parsed
                        if str(origin).strip()
                    ]

                except (
                    json.JSONDecodeError,
                    ValueError,
                ) as exc:
                    raise ValueError(
                        "ALLOWED_ORIGINS JSON must "
                        "contain a list of URLs."
                    ) from exc

            return [
                origin.strip().rstrip("/")
                for origin in raw_value.split(",")
                if origin.strip()
            ]

        raise ValueError(
            "ALLOWED_ORIGINS must be a list, "
            "JSON list, or comma-separated string."
        )

    @field_validator(
        "FRONTEND_URL"
    )
    @classmethod
    def normalise_frontend_url(
        cls,
        value: str,
    ) -> str:
        cleaned = (
            value.strip().rstrip("/")
        )

        if not cleaned:
            raise ValueError(
                "FRONTEND_URL cannot be empty."
            )

        return cleaned

    @field_validator(
        "ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    @classmethod
    def validate_access_token_expiry(
        cls,
        value: int,
    ) -> int:
        if value < 1:
            raise ValueError(
                "ACCESS_TOKEN_EXPIRE_MINUTES "
                "must be at least 1."
            )

        return value

    @field_validator(
        "REFRESH_TOKEN_EXPIRE_DAYS"
    )
    @classmethod
    def validate_refresh_token_expiry(
        cls,
        value: int,
    ) -> int:
        if value < 1:
            raise ValueError(
                "REFRESH_TOKEN_EXPIRE_DAYS "
                "must be at least 1."
            )

        if value > 365:
            raise ValueError(
                "REFRESH_TOKEN_EXPIRE_DAYS "
                "cannot exceed 365."
            )

        return value

    @field_validator(
        "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES"
    )
    @classmethod
    def validate_password_reset_expiry(
        cls,
        value: int,
    ) -> int:
        if value < 5:
            raise ValueError(
                "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES "
                "must be at least 5."
            )

        if value > 1440:
            raise ValueError(
                "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES "
                "cannot exceed 1440."
            )

        return value

    @field_validator(
        "FAILED_LOGIN_MAX_ATTEMPTS"
    )
    @classmethod
    def validate_failed_login_max_attempts(
        cls,
        value: int,
    ) -> int:
        if value < 3:
            raise ValueError(
                "FAILED_LOGIN_MAX_ATTEMPTS "
                "must be at least 3."
            )

        if value > 20:
            raise ValueError(
                "FAILED_LOGIN_MAX_ATTEMPTS "
                "cannot exceed 20."
            )

        return value

    @field_validator(
        "ACCOUNT_LOCKOUT_MINUTES"
    )
    @classmethod
    def validate_account_lockout_minutes(
        cls,
        value: int,
    ) -> int:
        if value < 1:
            raise ValueError(
                "ACCOUNT_LOCKOUT_MINUTES "
                "must be at least 1."
            )

        if value > 1440:
            raise ValueError(
                "ACCOUNT_LOCKOUT_MINUTES "
                "cannot exceed 1440."
            )

        return value

    @field_validator(
        "MAX_UPLOAD_SIZE_MB"
    )
    @classmethod
    def validate_upload_limit(
        cls,
        value: int,
    ) -> int:
        if value < 1 or value > 100:
            raise ValueError(
                "MAX_UPLOAD_SIZE_MB must be "
                "between 1 and 100."
            )

        return value

    @field_validator(
        "MAX_CV_PAGES"
    )
    @classmethod
    def validate_max_cv_pages(
        cls,
        value: int,
    ) -> int:
        if value < 1 or value > 500:
            raise ValueError(
                "MAX_CV_PAGES must be "
                "between 1 and 500."
            )

        return value

    @field_validator(
        "MAX_CV_TEXT_CHARACTERS"
    )
    @classmethod
    def validate_max_cv_text_characters(
        cls,
        value: int,
    ) -> int:
        if (
            value < 1_000
            or value > 2_000_000
        ):
            raise ValueError(
                "MAX_CV_TEXT_CHARACTERS must be "
                "between 1000 and 2000000."
            )

        return value

    @field_validator(
        "MAX_DOCX_UNCOMPRESSED_MB"
    )
    @classmethod
    def validate_docx_uncompressed_limit(
        cls,
        value: int,
    ) -> int:
        if value < 1 or value > 500:
            raise ValueError(
                "MAX_DOCX_UNCOMPRESSED_MB must be "
                "between 1 and 500."
            )

        return value

    @model_validator(
        mode="after"
    )
    def validate_production_settings(
        self,
    ):
        if (
            self.ENVIRONMENT
            == "production"
        ):
            unsafe_secrets = {
                "",
                "change-me-in-production",
                "secret",
                "password",
            }

            if (
                self.SECRET_KEY
                .strip()
                .lower()
                in unsafe_secrets
            ):
                raise ValueError(
                    "A secure SECRET_KEY must be "
                    "configured in production."
                )

            if (
                "postgres:password@"
                in self.DATABASE_URL.lower()
            ):
                raise ValueError(
                    "The default development "
                    "DATABASE_URL cannot be used "
                    "in production."
                )

            if not self.ALLOWED_ORIGINS:
                raise ValueError(
                    "At least one production frontend "
                    "origin must be configured."
                )

            if "*" in self.ALLOWED_ORIGINS:
                raise ValueError(
                    "Wildcard CORS origins are not "
                    "allowed in production."
                )

        return self

    @property
    def is_production(
        self,
    ) -> bool:
        return (
            self.ENVIRONMENT
            == "production"
        )

    @property
    def docs_enabled(
        self,
    ) -> bool:
        if self.is_production:
            return self.ENABLE_API_DOCS

        return True


settings = Settings()