from pydantic import BaseModel, Field, field_validator

from app.schemas.agent_contracts import Domain, QuestionScore


class OnboardingRequest(BaseModel):
    university: str = ""
    degree: str = ""
    graduation_year: int | None = Field(None, ge=1950, le=2050)
    career_interests: list[str] = Field(default_factory=list, max_length=10)
    personality_results: dict = Field(default_factory=dict)

    # Used only to generate the calibration MCQs below — never persisted.
    chosen_field: Domain
    self_assessment: list[QuestionScore] = Field(default_factory=list, max_length=20)

    @field_validator("career_interests")
    @classmethod
    def validate_career_interests(cls, v: list[str]) -> list[str]:
        cleaned = [item.strip() for item in v if item.strip()]
        if len(cleaned) != len(v):
            raise ValueError("career_interests must not contain empty values")
        return cleaned


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
