from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.insight import (
    GenerateWeeklyRequest,
    GenerateMonthlyRequest,
    InsightReportResponse,
    InsightReportListItem,
    WeeklyStatusResponse,
    InsightArchiveResponse,
)
from app.services.insight_service import insight_service

router = APIRouter(prefix="/api/insight", tags=["insight"])


@router.get("/weekly/status")
async def get_weekly_status(
    weekStart: str = Query(..., alias="weekStart", description="该周周一日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    """查询指定周是否已生成周报"""
    result = await insight_service.get_weekly_status(db, weekStart)
    return result


@router.get("/weekly")
async def get_weekly_report(
    weekStart: str = Query(..., alias="weekStart", description="该周周一日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    """获取指定周的周报数据"""
    report = await insight_service.get_weekly_report(db, weekStart)
    if not report:
        return None
    return _report_to_response(report)


@router.get("/monthly")
async def get_monthly_report(
    monthStart: str = Query(..., alias="monthStart", description="该月1号日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    """获取指定月的月报数据"""
    report = await insight_service.get_monthly_report(db, monthStart)
    if not report:
        return None
    return _report_to_response(report)


@router.get("/archive")
async def get_archive(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取洞察档案列表"""
    result = await insight_service.get_archive(db, page, size)
    return result


@router.get("/archive/{report_id}")
async def get_archive_detail(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取单份洞察报告详情"""
    report = await insight_service.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return _report_to_response(report)


@router.post("/generate/weekly", response_model=InsightReportResponse)
async def generate_weekly(
    body: GenerateWeeklyRequest,
    db: AsyncSession = Depends(get_db),
):
    """生成周报"""
    try:
        report = await insight_service.generate_weekly(db, body.week_start)
        return _report_to_response(report)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate/monthly", response_model=InsightReportResponse)
async def generate_monthly(
    body: GenerateMonthlyRequest,
    db: AsyncSession = Depends(get_db),
):
    """生成月报"""
    try:
        report = await insight_service.generate_monthly(db, body.month_start)
        return _report_to_response(report)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/archive/{report_id}", status_code=204)
async def delete_archive_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除洞察报告"""
    await insight_service.delete_report(db, report_id)


def _report_to_response(report) -> dict:
    """将 InsightReport 模型转为响应字典"""
    return {
        "id": report.id,
        "report_type": report.report_type.value,
        "date_start": report.date_start,
        "date_end": report.date_end,
        "summary": report.summary,
        "emotion_curve": report.emotion_curve,
        "keywords": report.keywords,
        "low_point": report.low_point,
        "high_point": report.high_point,
        "pattern": report.pattern,
        "core_theme": report.core_theme,
        "memory_count": report.memory_count,
        "is_read": report.is_read,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }