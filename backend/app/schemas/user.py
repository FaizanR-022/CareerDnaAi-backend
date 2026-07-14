from pydantic import BaseModel, Field, field_validator

from app.schemas.agent_contracts import Domain, QuestionScore


class OnboardingRequest(BaseModel):
    """university/degree/graduation_year/core_interests are already captured
    at signup — not re-asked here. Both fields below are used only to
    generate the calibration MCQs and are never persisted."""

    chosen_field: Domain
    self_assessment: list[QuestionScore] = Field(default_factory=list, max_length=20)


class UpdateUserRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=200)
    university: str | None = None
    degree: str | None = None
    graduation_year: int | None = Field(None, ge=1950, le=2050)
    core_interests: list[str] | None = Field(None, max_length=10)

    @field_validator("core_interests")
    @classmethod
    def validate_core_interests(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        cleaned = [item.strip() for item in v if item.strip()]
        if len(cleaned) != len(v):
            raise ValueError("core_interests must not contain empty values")
        return cleaned
