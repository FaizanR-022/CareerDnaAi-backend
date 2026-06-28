from pydantic import BaseModel


class ReportRequest(BaseModel):
    session_ids: list[str]
