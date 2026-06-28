from pydantic import BaseModel


class StartSessionRequest(BaseModel):
    domain: str = "pm"
    difficulty: str = "medium"


class ActionRequest(BaseModel):
    session_id: str
    user_action: str
