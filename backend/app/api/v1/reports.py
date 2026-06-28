from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user
from app.schemas.report import ReportRequest
from app.services import report_service

router = APIRouter(tags=["reports"])


@router.post("/report/generate")
def generate_report(req: ReportRequest, current_user: dict = Depends(get_current_user)):
    if not req.session_ids:
        raise HTTPException(status_code=400, detail="No session IDs provided")
    return report_service.generate_report(current_user["user_id"], req.session_ids)
