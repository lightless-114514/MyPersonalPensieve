from fastapi import APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.db.session import get_db
from app.models.memory import Memory

router = APIRouter()

from fastapi import Depends


@router.get("/api/graph")
async def get_knowledge_graph(db: AsyncSession = Depends(get_db)):
    """Return knowledge graph data from entities and relations."""
    from app.models.memory import KnowledgeEntity, MemoryEntity as ME, Relation
    from sqlalchemy.orm import selectinload

    # Get all entities with their memory associations
    entities_result = await db.execute(select(KnowledgeEntity))
    entities = entities_result.scalars().all()

    relations_result = await db.execute(select(Relation))
    relations = relations_result.scalars().all()

    nodes = []
    seen = set()
    for e in entities:
        if e.name not in seen:
            seen.add(e.name)
            group_map = {"PERSON": 1, "PLACE": 2, "ORG": 3, "EVENT": 4, "TOPIC": 5, "TECHNOLOGY": 6, "OTHER": 0}
            nodes.append({
                "id": e.id,
                "name": e.name,
                "type": e.type.value if e.type else "OTHER",
                "group": group_map.get(e.type.value if e.type else "OTHER", 0),
            })

    links = []
    for r in relations:
        links.append({
            "source": r.source_entity_id,
            "target": r.target_entity_id,
            "type": r.relation_type,
            "strength": 1.0,
        })

    return {"nodes": nodes, "links": links}


@router.get("/api/analytics/sentiment")
async def get_sentiment_trend(days: int = Query(30, ge=1, le=365), db: AsyncSession = Depends(get_db)):
    """Return sentiment trend data for the past N days."""
    from datetime import datetime, timedelta

    start_date = datetime.utcnow() - timedelta(days=days)

    memories_result = await db.execute(
        select(Memory).where(
            Memory.created_at >= start_date,
            Memory.sentiment.isnot(None),
        ).order_by(Memory.created_at)
    )
    memories = memories_result.scalars().all()

    # Group by date
    trend_map = {}
    for m in memories:
        date_key = m.created_at.strftime("%Y-%m-%d") if m.created_at else ""
        if date_key not in trend_map:
            trend_map[date_key] = {"positive": 0, "negative": 0, "neutral": 0, "total": 0}
        trend_map[date_key]["total"] += 1
        sentiment = m.sentiment.value if m.sentiment else "NEUTRAL"
        if sentiment == "POSITIVE":
            trend_map[date_key]["positive"] += 1
        elif sentiment == "NEGATIVE":
            trend_map[date_key]["negative"] += 1
        else:
            trend_map[date_key]["neutral"] += 1

    result = []
    for date_key in sorted(trend_map.keys()):
        d = trend_map[date_key]
        t = d["total"] or 1
        avg = (d["positive"] - d["negative"]) / t
        result.append({
            "date": date_key,
            "positive": d["positive"],
            "negative": d["negative"],
            "neutral": d["neutral"],
            "average": round(avg, 2),
        })

    return result
