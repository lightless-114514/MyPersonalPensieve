import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.memory import Memory
from app.schemas.compare import CompareRequest, CompareResult, ComparePoint
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/compare", tags=["compare"])


def _format_memory(mem: Memory) -> dict:
    """格式化记忆为简洁字典"""
    return {
        "id": mem.id,
        "title": mem.title,
        "content": mem.content[:500],  # 截断避免过长
        "tags": [t.tag for t in mem.tags] if mem.tags else [],
        "big_tag": mem.big_tag.value if mem.big_tag else None,
        "sentiment": mem.sentiment.value if mem.sentiment else None,
        "created_at": mem.created_at.isoformat() if mem.created_at else None,
    }


async def _fetch_memories(db: AsyncSession, ids: list[str]) -> list[Memory]:
    """批量获取记忆"""
    stmt = select(Memory).where(Memory.id.in_(ids)).options(selectinload(Memory.tags)).order_by(Memory.created_at.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _compute_time_span(sources: list[Memory], targets: list[Memory]) -> tuple[int | None, str | None, str | None]:
    """计算时间跨度"""
    all_dates = []
    for m in sources + targets:
        if m.created_at:
            all_dates.append(m.created_at)
    if not all_dates:
        return None, None, None
    earliest = min(all_dates)
    latest = max(all_dates)
    span = (latest - earliest).days
    return span, earliest.strftime("%Y-%m-%d"), latest.strftime("%Y-%m-%d")


async def _ai_compare(source_data: list[dict], target_data: list[dict]) -> dict:
    """调用LLM生成对比结果"""
    prompt = f"""你是一位专业的个人成长分析助手。请对比以下两组记忆，分析它们的相同点和变化点。

## 源记忆（较早/左侧）：
{json.dumps(source_data, ensure_ascii=False, indent=2)}

## 目标记忆（较晚/右侧）：
{json.dumps(target_data, ensure_ascii=False, indent=2)}

请按以下JSON格式返回分析结果（不要markdown代码块）：
{{
  "similarities": [
    {{"content": "相同点描述", "source_refs": ["关联的源记忆标题"], "target_refs": ["关联的目标记忆标题"]}}
  ],
  "differences": [
    {{"content": "变化点描述", "source_refs": ["关联的源记忆标题"], "target_refs": ["关联的目标记忆标题"]}}
  ],
  "source_summary": "源记忆整体概要（一句话）",
  "target_summary": "目标记忆整体概要（一句话）",
  "growth_insight": "基于对比的成长洞察与建议（2-3句话，对自我成长类用户极其有用）"
}}

分析要点：
1. 相同点：关注持续的兴趣、价值观、行为模式
2. 变化点：关注认知升级、态度转变、技能成长、视角变化
3. 成长洞察：从变化趋势中提炼个人成长轨迹和建议
4. 每个对比点尽量引用具体的记忆标题作为参考"""

    try:
        raw = await asyncio.wait_for(
            llm_service.chat([
                {"role": "system", "content": "你是一位专业的个人成长分析助手，擅长对比分析记忆并提炼成长洞察。只返回纯JSON，不要markdown代码块。"},
                {"role": "user", "content": prompt},
            ]),
            timeout=90.0,
        )
        # 清理markdown代码块
        clean = raw.strip().strip("`").strip()
        if clean.startswith("json"):
            clean = clean[4:].strip()
        clean = clean.strip("`").strip()
        return json.loads(clean)
    except Exception as e:
        print(f"AI compare error: {e}")
        return {
            "similarities": [],
            "differences": [],
            "source_summary": "",
            "target_summary": "",
            "growth_insight": None,
        }


@router.post("", response_model=CompareResult)
async def compare_memories(
    body: CompareRequest,
    db: AsyncSession = Depends(get_db),
):
    """对比两组记忆，AI生成相同点和变化点分析"""
    if not body.source_ids or not body.target_ids:
        raise HTTPException(status_code=400, detail="源记忆和目标记忆均不能为空")

    # 检查ID不能重叠
    overlap = set(body.source_ids) & set(body.target_ids)
    if overlap:
        raise HTTPException(status_code=400, detail=f"源记忆和目标记忆不能重叠: {overlap}")

    # 获取记忆数据
    sources = await _fetch_memories(db, body.source_ids)
    targets = await _fetch_memories(db, body.target_ids)

    if not sources:
        raise HTTPException(status_code=404, detail="未找到源记忆")
    if not targets:
        raise HTTPException(status_code=404, detail="未找到目标记忆")

    # 格式化记忆数据
    source_data = [_format_memory(m) for m in sources]
    target_data = [_format_memory(m) for m in targets]

    # 计算时间跨度
    time_span_days, earliest_date, latest_date = _compute_time_span(sources, targets)

    # 收集标签
    source_tags = list(set(tag.tag for m in sources for tag in (m.tags or [])))
    target_tags = list(set(tag.tag for m in targets for tag in (m.tags or [])))

    # AI对比
    ai_result = await _ai_compare(source_data, target_data)

    # 构建结果
    similarities = [ComparePoint(**p) for p in ai_result.get("similarities", [])]
    differences = [ComparePoint(**p) for p in ai_result.get("differences", [])]

    return CompareResult(
        similarities=similarities,
        differences=differences,
        source_summary=ai_result.get("source_summary", ""),
        target_summary=ai_result.get("target_summary", ""),
        time_span_days=time_span_days,
        earliest_date=earliest_date,
        latest_date=latest_date,
        source_count=len(sources),
        target_count=len(targets),
        source_tags=source_tags,
        target_tags=target_tags,
        growth_insight=ai_result.get("growth_insight"),
    )