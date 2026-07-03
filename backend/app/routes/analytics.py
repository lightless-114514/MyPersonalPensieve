from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from app.db.session import get_db
from app.models.memory import Memory, BigTag, MemoryTag

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


@router.get("/api/analytics/heatmap")
async def get_heatmap(
    year: int = Query(None, description="Year, defaults to current year"),
    db: AsyncSession = Depends(get_db),
):
    """Return writing heatmap data: one entry per day with word_count and memory_count."""
    from datetime import datetime, timedelta
    import calendar

    target_year = year or datetime.utcnow().year
    start_date = datetime(target_year, 1, 1)
    end_date = datetime(target_year, 12, 31)

    # Query daily word count and memory count
    stmt = (
        select(
            func.date(Memory.created_at).label("date"),
            func.count(Memory.id).label("memory_count"),
            func.sum(func.length(Memory.content)).label("word_count"),
        )
        .where(
            Memory.created_at >= start_date,
            Memory.created_at <= end_date,
        )
        .group_by(func.date(Memory.created_at))
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Build a lookup dict
    data_map = {}
    for row in rows:
        date_str = row.date.strftime("%Y-%m-%d") if hasattr(row.date, "strftime") else str(row.date)
        data_map[date_str] = {
            "date": date_str,
            "memory_count": row.memory_count,
            "word_count": int(row.word_count or 0),
        }

    # Fill all days of the year (including days with no data)
    all_days = []
    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        if date_str in data_map:
            all_days.append(data_map[date_str])
        else:
            all_days.append({
                "date": date_str,
                "memory_count": 0,
                "word_count": 0,
            })
        current += timedelta(days=1)

    return all_days


@router.get("/api/analytics/wordcloud")
async def get_wordcloud(
    period: str = Query("month", description="Period: month or year"),
    limit: int = Query(80, ge=10, le=200, description="Max words to return"),
    db: AsyncSession = Depends(get_db),
):
    """Return high-frequency tags/words for word cloud visualization."""
    from datetime import datetime, timedelta

    if period == "year":
        start_date = datetime.utcnow() - timedelta(days=365)
    else:
        start_date = datetime.utcnow() - timedelta(days=30)

    # Get tags from memories in the period, grouped by tag with count
    stmt = (
        select(
            MemoryTag.tag.label("word"),
            func.count(MemoryTag.memory_id).label("count"),
        )
        .join(Memory, MemoryTag.memory_id == Memory.id)
        .where(Memory.created_at >= start_date)
        .group_by(MemoryTag.tag)
        .order_by(desc(func.count(MemoryTag.memory_id)))
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [{"word": row.word, "count": row.count} for row in rows]


@router.get("/api/analytics/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
):
    """Return summary statistics: total memories, total words, streak days, this month count."""
    from datetime import datetime, timedelta

    # Total memories
    total_result = await db.execute(select(func.count(Memory.id)))
    total_memories = total_result.scalar() or 0

    # Total word count (sum of content length)
    words_result = await db.execute(select(func.sum(func.length(Memory.content))))
    total_words = int(words_result.scalar() or 0)

    # This month count
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_result = await db.execute(
        select(func.count(Memory.id)).where(Memory.created_at >= month_start)
    )
    this_month = month_result.scalar() or 0

    # Calculate streak (consecutive days with at least one memory, counting back from today)
    streak_result = await db.execute(
        select(func.date(Memory.created_at).label("d"))
        .group_by(func.date(Memory.created_at))
        .order_by(desc(func.date(Memory.created_at)))
    )
    dates_with_memories = [row.d for row in streak_result.all()]

    streak = 0
    if dates_with_memories:
        today = datetime.utcnow().date()
        # Check if today or yesterday has memories (allow today not yet written)
        first_date = dates_with_memories[0]
        if hasattr(first_date, "date"):
            first_date = first_date.date() if hasattr(first_date, "date") else first_date

        # Start from today or yesterday
        check_date = today
        if check_date not in dates_with_memories:
            check_date = today - timedelta(days=1)

        for d in dates_with_memories:
            d_date = d.date() if hasattr(d, "date") else d
            if d_date == check_date:
                streak += 1
                check_date -= timedelta(days=1)
            elif d_date < check_date:
                break

    return {
        "total_memories": total_memories,
        "total_words": total_words,
        "streak_days": streak,
        "this_month": this_month,
    }
