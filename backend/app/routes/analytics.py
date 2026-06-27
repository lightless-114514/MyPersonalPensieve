from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.db.session import get_db
from app.models.memory import Memory, BigTag

router = APIRouter()


@router.get("/api/graph")
async def get_knowledge_graph(
    big_tag: str = Query(None, description="Filter by big_tag"),
    db: AsyncSession = Depends(get_db),
):
    """Return knowledge graph data from entities and relations. Optionally filter by big_tag."""
    from app.models.memory import KnowledgeEntity, MemoryEntity as ME, Relation

    # If big_tag filter is provided, only include entities from memories with that big_tag
    if big_tag:
        try:
            bt = BigTag(big_tag.upper())
        except ValueError:
            return {"nodes": [], "links": []}

        # Get memory IDs with this big_tag
        mem_ids_result = await db.execute(
            select(Memory.id).where(Memory.big_tag == bt)
        )
        mem_ids = set(row[0] for row in mem_ids_result.all())

        if not mem_ids:
            return {"nodes": [], "links": []}

        # Get entities linked to these memories
        me_result = await db.execute(
            select(ME.entity_id).where(ME.memory_id.in_(mem_ids)).distinct()
        )
        entity_ids = set(row[0] for row in me_result.all())

        if not entity_ids:
            return {"nodes": [], "links": []}

        entities_result = await db.execute(
            select(KnowledgeEntity).where(KnowledgeEntity.id.in_(entity_ids))
        )
        entities = entities_result.scalars().all()

        # Relations between these entities
        relations_result = await db.execute(
            select(Relation).where(
                Relation.source_entity_id.in_(entity_ids),
                Relation.target_entity_id.in_(entity_ids),
            )
        )
        relations = relations_result.scalars().all()
    else:
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
async def get_sentiment_trend(
    days: int = Query(30, ge=1, le=365),
    big_tag: str = Query(None, description="Filter by big_tag"),
    db: AsyncSession = Depends(get_db),
):
    """Return sentiment trend data for the past N days. Optionally filter by big_tag."""
    from datetime import datetime, timedelta

    start_date = datetime.utcnow() - timedelta(days=days)

    stmt = select(Memory).where(
        Memory.created_at >= start_date,
        Memory.sentiment.isnot(None),
    )

    if big_tag:
        try:
            bt = BigTag(big_tag.upper())
            stmt = stmt.where(Memory.big_tag == bt)
        except ValueError:
            return []

    stmt = stmt.order_by(Memory.created_at)

    memories_result = await db.execute(stmt)
    memories = memories_result.scalars().all()

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
