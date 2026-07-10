from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.schemas.report import CareerDnaReportResponse, ReportGenerateRequest
from app.services import simulation_report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=CareerDnaReportResponse, status_code=201)
def generate_report(req: ReportGenerateRequest, current_user: dict = Depends(get_current_user)):
    return simulation_report_service.generate_report(current_user, req.simulation_session_ids)


@router.get("", response_model=list[CareerDnaReportResponse])
def list_my_reports(current_user: dict = Depends(get_current_user)):
    return simulation_report_service.list_my_reports(current_user)


@router.get("/{report_id}", response_model=CareerDnaReportResponse)
def get_report(report_id: str, current_user: dict = Depends(get_current_user)):
    return simulation_report_service.get_report(report_id, current_user)
