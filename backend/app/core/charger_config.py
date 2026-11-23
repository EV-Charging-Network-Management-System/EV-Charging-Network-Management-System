"""Typed configuration for opt-in charger connections."""

from pydantic import BaseModel, Field, SecretStr, field_validator


class ChargerDevice(BaseModel):
    password: SecretStr
    driver_tags: dict[str, int] = Field(default_factory=dict)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 24:
            raise ValueError("Charger passwords must contain at least 24 characters.")
        return value
