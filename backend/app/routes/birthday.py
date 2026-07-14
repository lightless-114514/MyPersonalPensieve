"""生日功能相关 API 路由

所有生日数据仅存储在客户端本地，此路由仅提供 AI 生日祝福生成功能。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.memory import Memory, PrivacyStatus
from app.services.llm_service import llm_service
from pydantic import BaseModel

router = APIRouter(prefix="/api/birthday", tags=["birthday"])


class BirthdayWishRequest(BaseModel):
    """生日祝福请求 - 不包含任何生日日期信息，保护隐私"""
    pass


class BirthdayWishResponse(BaseModel):
    """生日祝福响应"""
    wish: str
    fallback: bool = False  # 是否为回退文案（无日记数据时）


FALLBACK_WISHES = [
    "生日快乐！愿新的一岁，每一天都充满阳光与惊喜。 🌟",
    "又长一岁啦！愿你在新的一岁里，遇见更好的自己。 ✨",
    "生日快乐！愿你的生活像蛋糕一样甜蜜，像气球一样自由。 🎂",
    "新的一岁，愿你被这世界温柔以待，所有美好如期而至。 🎁",
    "生日快乐！愿你在记录与回忆中，发现生活的每一份美好。 📝",
]


async def _generate_birthday_wish(db: AsyncSession) -> str:
    """基于过去一年的日记数据生成 AI 生日祝福"""
    from datetime import datetime, timedelta

    one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    # 获取过去一年「纳入分析」的日记
    stmt = (
        select(Memory)
        .where(
            and_(
                Memory.privacy_status == PrivacyStatus.ANALYZE,
                func.date(Memory.created_at) >= one_year_ago,
                func.date(Memory.created_at) <= today,
            )
        )
        .order_by(Memory.created_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    memories = list(result.scalars().all())

    if not memories:
        raise ValueError("no_memories")

    # 构建日记摘要
    memory_data = []
    for m in memories:
        memory_data.append({
            "date": m.created_at.strftime("%Y-%m-%d"),
            "title": m.title,
            "content_preview": m.content[:150] if m.content else "",
            "sentiment": m.sentiment.value if m.sentiment else "NEUTRAL",
        })

    prompt = f"""你是一位温暖的朋友。今天是用户的生日，请基于以下过去一年的日记摘要，为用户生成一段生日祝福。

要求：
- 不少于 50 字
- 引用用户过去一年的成长亮点或关键经历
- 语气温暖真诚，像朋友在耳边说话
- 不要使用"根据日记"之类的元描述
- 适当提及用户记录生活的习惯

过去一年的日记摘要：
{__import__('json').dumps(memory_data, ensure_ascii=False, indent=2)[:3000]}

请直接输出祝福文本，不要 JSON 格式，不要标题。"""

    messages = [
        {"role": "system", "content": "你是一位温暖真诚的朋友，擅长从生活记录中发现闪光点，为朋友送上走心的生日祝福。"},
        {"role": "user", "content": prompt},
    ]
    return await llm_service.chat(messages)


@router.post("/wish", response_model=BirthdayWishResponse)
async def generate_birthday_wish(
    db: AsyncSession = Depends(get_db),
):
    """生成 AI 生日祝福

    此 API 不接收任何生日日期信息，仅基于用户日记数据生成祝福。
    生日日期完全由客户端本地管理，保护用户隐私。
    """
    try:
        wish = await _generate_birthday_wish(db)
        return BirthdayWishResponse(wish=wish, fallback=False)
    except ValueError as e:
        if str(e) == "no_memories":
            # 过去一年无日记数据，回退至预设文案
            import random
            wish = random.choice(FALLBACK_WISHES)
            return BirthdayWishResponse(wish=wish, fallback=True)
        raise
    except Exception as e:
        # AI 生成失败，回退至预设文案
        import random
        wish = random.choice(FALLBACK_WISHES)
        return BirthdayWishResponse(wish=wish, fallback=True)