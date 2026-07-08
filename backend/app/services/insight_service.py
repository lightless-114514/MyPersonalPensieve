"""洞察报告生成服务：周报 / 月报"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory, InsightReport, InsightType, PrivacyStatus
from app.services.llm_service import llm_service


def _week_range(date_str: str) -> tuple[str, str]:
    """给定日期字符串，返回该周周一和周日的日期字符串"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = dt.weekday()  # 0=Monday
    monday = dt - timedelta(days=weekday)
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


def _month_range(date_str: str) -> tuple[str, str]:
    """给定日期字符串，返回该月第一天和最后一天的日期字符串"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    first_day = dt.replace(day=1)
    if dt.month == 12:
        last_day = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = dt.replace(month=dt.month + 1, day=1) - timedelta(days=1)
    return first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")


class InsightService:

    async def get_weekly_status(
        self, db: AsyncSession, week_start: str
    ) -> dict:
        """查询指定周的周报状态"""
        start, end = _week_range(week_start)
        stmt = select(InsightReport).where(
            and_(
                InsightReport.report_type == InsightType.WEEKLY,
                InsightReport.date_start == start,
                InsightReport.date_end == end,
            )
        )
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if report:
            # 检查该周是否有新日记（在报告生成之后创建的）
            new_mem_stmt = select(func.count(Memory.id)).where(
                and_(
                    Memory.privacy_status == PrivacyStatus.ANALYZE,
                    func.date(Memory.created_at) >= start,
                    func.date(Memory.created_at) <= end,
                    Memory.created_at > report.created_at,
                )
            )
            new_count = (await db.execute(new_mem_stmt)).scalar() or 0
            return {
                "week_start": start,
                "exists": True,
                "report_id": report.id,
                "has_new_memories": new_count > 0,
            }

        return {
            "week_start": start,
            "exists": False,
            "report_id": None,
            "has_new_memories": False,
        }

    async def get_analysable_memories(
        self, db: AsyncSession, date_start: str, date_end: str
    ) -> list[Memory]:
        """获取指定日期范围内「纳入分析」的日记"""
        stmt = (
            select(Memory)
            .where(
                and_(
                    Memory.privacy_status == PrivacyStatus.ANALYZE,
                    func.date(Memory.created_at) >= date_start,
                    func.date(Memory.created_at) <= date_end,
                )
            )
            .order_by(Memory.created_at)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def generate_weekly(
        self, db: AsyncSession, week_start: str
    ) -> InsightReport:
        """生成周报"""
        start, end = _week_range(week_start)

        # 检查是否已存在
        existing_stmt = select(InsightReport).where(
            and_(
                InsightReport.report_type == InsightType.WEEKLY,
                InsightReport.date_start == start,
                InsightReport.date_end == end,
            )
        )
        existing = (await db.execute(existing_stmt)).scalar_one_or_none()

        # 获取日记数据
        memories = await self.get_analysable_memories(db, start, end)
        if not memories:
            raise ValueError("该时间段暂无可用数据")

        # 构建 LLM 输入：仅摘要 + 情绪值
        memory_data = []
        for m in memories:
            memory_data.append({
                "date": m.created_at.strftime("%Y-%m-%d"),
                "title": m.title,
                "content_preview": m.content[:200] if m.content else "",
                "sentiment": m.sentiment.value if m.sentiment else "NEUTRAL",
                "sentiment_score": m.sentiment_score or 0.5,
            })

        # 调用 LLM 生成周报
        prompt = self._build_weekly_prompt(memory_data, start, end)
        llm_result = await self._call_llm(prompt)

        # 解析结果
        parsed = self._parse_weekly_result(llm_result, memory_data)

        if existing:
            # 覆盖已有周报
            existing.summary = parsed["summary"]
            existing.emotion_curve = json.dumps(parsed["emotion_curve"], ensure_ascii=False)
            existing.keywords = json.dumps(parsed["keywords"], ensure_ascii=False)
            existing.low_point = json.dumps(parsed["low_point"], ensure_ascii=False)
            existing.high_point = json.dumps(parsed["high_point"], ensure_ascii=False)
            existing.memory_count = len(memories)
            existing.updated_at = datetime.now()
            await db.commit()
            await db.refresh(existing)
            return existing

        # 新建周报
        report = InsightReport(
            id=str(uuid.uuid4()),
            report_type=InsightType.WEEKLY,
            date_start=start,
            date_end=end,
            summary=parsed["summary"],
            emotion_curve=json.dumps(parsed["emotion_curve"], ensure_ascii=False),
            keywords=json.dumps(parsed["keywords"], ensure_ascii=False),
            low_point=json.dumps(parsed["low_point"], ensure_ascii=False),
            high_point=json.dumps(parsed["high_point"], ensure_ascii=False),
            memory_count=len(memories),
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report

    async def generate_monthly(
        self, db: AsyncSession, month_start: str
    ) -> InsightReport:
        """生成月报（两步法优化 Token）"""
        start, end = _month_range(month_start)

        # 获取日记数据
        memories = await self.get_analysable_memories(db, start, end)
        if not memories:
            raise ValueError("该时间段暂无可用数据")

        # 第一步：按周分组，压缩为周代表摘要
        weekly_summaries = self._group_by_week(memories)

        # 第二步：调用 LLM 生成月报
        prompt = self._build_monthly_prompt(weekly_summaries, start, end)
        llm_result = await self._call_llm(prompt)

        # 解析结果
        parsed = self._parse_monthly_result(llm_result, weekly_summaries)

        # 月报允许重复生成，每次创建新记录
        report = InsightReport(
            id=str(uuid.uuid4()),
            report_type=InsightType.MONTHLY,
            date_start=start,
            date_end=end,
            summary=parsed["summary"],
            emotion_curve=json.dumps(parsed["emotion_curve"], ensure_ascii=False),
            keywords=json.dumps(parsed["keywords"], ensure_ascii=False),
            low_point=json.dumps(parsed["low_point"], ensure_ascii=False),
            high_point=json.dumps(parsed["high_point"], ensure_ascii=False),
            pattern=parsed.get("pattern", ""),
            core_theme=parsed.get("core_theme", ""),
            memory_count=len(memories),
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report

    async def get_archive(
        self, db: AsyncSession, page: int = 0, size: int = 20
    ) -> dict:
        """获取洞察档案列表"""
        count_stmt = select(func.count(InsightReport.id))
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(InsightReport)
            .order_by(desc(InsightReport.created_at))
            .offset(page * size)
            .limit(size)
        )
        result = await db.execute(stmt)
        reports = list(result.scalars().all())

        return {
            "total": total,
            "items": [self._report_to_list_item(r) for r in reports],
        }

    async def get_report_by_id(
        self, db: AsyncSession, report_id: str
    ) -> Optional[InsightReport]:
        """获取单份报告详情，并标记为已读"""
        stmt = select(InsightReport).where(InsightReport.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()
        if report and not report.is_read:
            report.is_read = True
            await db.commit()
            await db.refresh(report)
        return report

    async def delete_report(
        self, db: AsyncSession, report_id: str
    ) -> None:
        """删除洞察报告"""
        stmt = select(InsightReport).where(InsightReport.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()
        if report:
            await db.delete(report)
            await db.commit()

    async def get_weekly_report(
        self, db: AsyncSession, week_start: str
    ) -> Optional[InsightReport]:
        """获取指定周的周报数据"""
        start, end = _week_range(week_start)
        stmt = select(InsightReport).where(
            and_(
                InsightReport.report_type == InsightType.WEEKLY,
                InsightReport.date_start == start,
                InsightReport.date_end == end,
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_monthly_report(
        self, db: AsyncSession, month_start: str
    ) -> Optional[InsightReport]:
        """获取指定月的月报数据（最新的）"""
        start, end = _month_range(month_start)
        stmt = (
            select(InsightReport)
            .where(
                and_(
                    InsightReport.report_type == InsightType.MONTHLY,
                    InsightReport.date_start == start,
                    InsightReport.date_end == end,
                )
            )
            .order_by(desc(InsightReport.created_at))
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    # ---- 私有方法 ----

    def _group_by_week(self, memories: list[Memory]) -> list[dict]:
        """按周分组日记，生成周代表摘要"""
        weeks: dict[str, list] = {}
        for m in memories:
            dt = m.created_at
            monday = (dt - timedelta(days=dt.weekday())).strftime("%Y-%m-%d")
            if monday not in weeks:
                weeks[monday] = []
            weeks[monday].append({
                "date": dt.strftime("%Y-%m-%d"),
                "title": m.title,
                "content_preview": m.content[:200] if m.content else "",
                "sentiment": m.sentiment.value if m.sentiment else "NEUTRAL",
                "sentiment_score": m.sentiment_score or 0.5,
            })

        result = []
        for week_start, items in sorted(weeks.items()):
            avg_score = sum(i["sentiment_score"] for i in items) / len(items) if items else 0.5
            titles = "; ".join(i["title"] for i in items[:5])
            result.append({
                "week_start": week_start,
                "count": len(items),
                "avg_sentiment_score": round(avg_score, 2),
                "titles_summary": titles[:100],
            })
        return result

    def _build_weekly_prompt(self, memory_data: list[dict], start: str, end: str) -> str:
        return f"""你是一位自我洞察分析师。请根据以下日记数据，生成一份周报分析。

时间范围：{start} 至 {end}

日记数据：
{json.dumps(memory_data, ensure_ascii=False, indent=2)}

请返回纯 JSON 格式（不要 markdown 代码块），包含以下字段：
{{
  "summary": "一句话总结本周整体状态",
  "emotion_curve": [{{"date": "YYYY-MM-DD", "score": 0.0-1.0}}],
  "keywords": ["关键词1", "关键词2", ...],  // TOP 5
  "low_point": {{"date": "YYYY-MM-DD", "title": "标题", "preview": "摘要"}},
  "high_point": {{"date": "YYYY-MM-DD", "title": "标题", "preview": "摘要"}}
}}

注意：
- emotion_curve 每天一个数据点，没有日记的日期用前后插值
- keywords 最多5个
- low_point 和 high_point 必须来自实际日记数据"""

    def _build_monthly_prompt(self, weekly_summaries: list[dict], start: str, end: str) -> str:
        return f"""你是一位自我洞察分析师。请根据以下按周汇总的日记数据，生成一份月报分析。

时间范围：{start} 至 {end}

按周汇总数据：
{json.dumps(weekly_summaries, ensure_ascii=False, indent=2)}

请返回纯 JSON 格式（不要 markdown 代码块），包含以下字段：
{{
  "summary": "一句话总结本月核心主题",
  "emotion_curve": [{{"week_start": "YYYY-MM-DD", "avg_score": 0.0-1.0}}],
  "keywords": ["关键词1", "关键词2", ...],  // TOP 10
  "low_point": {{"week_start": "YYYY-MM-DD", "titles_summary": "该周标题摘要"}},
  "high_point": {{"week_start": "YYYY-MM-DD", "titles_summary": "该周标题摘要"}},
  "pattern": "本月显著模式描述",
  "core_theme": "本月核心主题一句话"
}}

注意：
- emotion_curve 每周一个数据点
- keywords 最多10个
- pattern 描述情绪变化规律，如"每到周一情绪走低，周四回升" """

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        messages = [
            {"role": "system", "content": "你是一位专业的自我洞察分析师，擅长从日记数据中提取情绪模式、关键词和深层洞察。请始终返回纯 JSON 格式。"},
            {"role": "user", "content": prompt},
        ]
        return await llm_service.chat(messages)

    def _parse_weekly_result(self, raw: str, memory_data: list[dict]) -> dict:
        """解析周报 LLM 返回"""
        try:
            clean = raw.strip().strip("`").strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
            clean = clean.strip("`").strip()
            data = json.loads(clean)
            return {
                "summary": data.get("summary", ""),
                "emotion_curve": data.get("emotion_curve", []),
                "keywords": data.get("keywords", []),
                "low_point": data.get("low_point", {}),
                "high_point": data.get("high_point", {}),
            }
        except (json.JSONDecodeError, TypeError):
            # Fallback：手动构建简单结果
            scores = [m["sentiment_score"] for m in memory_data]
            avg = sum(scores) / len(scores) if scores else 0.5
            return {
                "summary": raw[:200] if raw else "分析完成",
                "emotion_curve": [{"date": m["date"], "score": m["sentiment_score"]} for m in memory_data],
                "keywords": [],
                "low_point": {},
                "high_point": {},
            }

    def _parse_monthly_result(self, raw: str, weekly_summaries: list[dict]) -> dict:
        """解析月报 LLM 返回"""
        try:
            clean = raw.strip().strip("`").strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
            clean = clean.strip("`").strip()
            data = json.loads(clean)
            return {
                "summary": data.get("summary", ""),
                "emotion_curve": data.get("emotion_curve", []),
                "keywords": data.get("keywords", []),
                "low_point": data.get("low_point", {}),
                "high_point": data.get("high_point", {}),
                "pattern": data.get("pattern", ""),
                "core_theme": data.get("core_theme", ""),
            }
        except (json.JSONDecodeError, TypeError):
            return {
                "summary": raw[:200] if raw else "分析完成",
                "emotion_curve": [{"week_start": w["week_start"], "avg_score": w["avg_sentiment_score"]} for w in weekly_summaries],
                "keywords": [],
                "low_point": {},
                "high_point": {},
                "pattern": "",
                "core_theme": "",
            }

    @staticmethod
    def _report_to_list_item(r: InsightReport) -> dict:
        return {
            "id": r.id,
            "report_type": r.report_type.value,
            "date_start": r.date_start,
            "date_end": r.date_end,
            "summary": r.summary,
            "memory_count": r.memory_count,
            "is_read": r.is_read,
            "created_at": r.created_at,
        }


insight_service = InsightService()