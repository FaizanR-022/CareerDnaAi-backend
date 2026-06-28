from pydantic import BaseModel


class OnboardingRequest(BaseModel):
    university: str = ""
    degree: str = ""
    graduation_year: str = ""
    career_interests: list[str] = []
    personality_results: dict = {}
    self_rated_pm: int = 3
    self_rated_sqa: int = 3
    self_rated_data: int = 3
    self_rated_frontend: int = 3
    self_rated_backend: int = 3
