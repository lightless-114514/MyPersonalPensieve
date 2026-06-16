import json
import math
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.memory import Memory, MemoryTag, MemoryType
from app.schemas.memory import MemoryRequest, MemoryResponse, PagedResponse
from app.services.redis_service import redis_service
from app.services.qdrant_service import qdrant_service
from app.services.llm_service import llm_service


class MemoryService:
    async def create(self, db: AsyncSession, request: MemoryRequest) -> MemoryResponse:
        mem_type = MemoryType(request.type.upper()) if request.type else MemoryType.TEXT
        memory = Memory(
            title=request.title,
            content=request.content,
            type=mem_type,
            source_url=request.source_url,
        )
        db.add(memory)
        await db.flush()

        # Add tags
        for tag in request.tags or []:
            db.add(MemoryTag(memory_id=memory.id, tag=tag))

        await db.commit()
        await db.refresh(memory, attribute_names=["tags"])

        # Evict cache
        await redis_service.evict_recent_memories()

        # Background: generate embedding and extract entities
        # (in production this would be a BackgroundTask or Celery task)
        try:
            embedding = await llm_service.generate_embedding(request.content)
            qdrant_service.upsert_vectors([
                {"id": memory.id, "vector": embedding, "payload": {"title": request.title, "type": request.type}}
            ])
        except Exception:
            pass  # Don't block the response if LLM/Qdrant fails

        return self._to_response(memory)

    async def get_all(
        self, db: AsyncSession, page: int = 0, size: int = 20
    ) -> PagedResponse:
        count_query = select(func.count(Memory.id))
        total = (await db.execute(count_query)).scalar() or 0

        query = (
            select(Memory)
            .options(selectinload(Memory.tags))
            .order_by(desc(Memory.created_at))
            .offset(page * size)
            .limit(size)
        )
        result = await db.execute(query)
        memories = result.scalars().all()

        total_pages = math.ceil(total / size) if total > 0 else 1

        return PagedResponse(
            content=[self._to_response(m) for m in memories],
            page=page,
            size=size,
            total_elements=total,
            total_pages=total_pages,
            last=(page + 1) * size >= total,
            first=page == 0,
        )

    async def get_recent(self, db: AsyncSession, limit: int = 10) -> list[MemoryResponse]:
        cached = await redis_service.get_recent_memories()
        if cached:
            try:
                data = json.loads(cached)
                return [MemoryResponse(**item) for item in data]
            except (json.JSONDecodeError, TypeError):
                pass

        query = (
            select(Memory)
            .options(selectinload(Memory.tags))
            .order_by(desc(Memory.created_at))
            .limit(limit)
        )
        result = await db.execute(query)
        memories = result.scalars().all()

        responses = [self._to_response(m) for m in memories]

        try:
            await redis_service.cache_recent_memories(
                json.dumps([r.model_dump(mode="json") for r in responses])
            )
        except Exception:
            pass

        return responses

    async def get_by_id(self, db: AsyncSession, memory_id: str) -> MemoryResponse:
        query = (
            select(Memory)
            .options(selectinload(Memory.tags))
            .where(Memory.id == memory_id)
        )
        result = await db.execute(query)
        memory = result.scalar_one_or_none()
        if not memory:
            raise ValueError(f"Memory not found: {memory_id}")
        return self._to_response(memory)

    async def delete(self, db: AsyncSession, memory_id: str) -> None:
        memory = await db.get(Memory, memory_id)
        if not memory:
            raise ValueError(f"Memory not found: {memory_id}")
        await db.delete(memory)
        await db.commit()
        await redis_service.evict_recent_memories()

    @staticmethod
    def _to_response(m: Memory) -> MemoryResponse:
        return MemoryResponse(
            id=m.id,
            title=m.title,
            content=m.content,
            type=m.type.value if m.type else "TEXT",
            source_url=m.source_url,
            file_path=m.file_path,
            sentiment=m.sentiment.value if m.sentiment else None,
            sentiment_score=m.sentiment_score,
            processing_status=m.processing_status.value if m.processing_status else "PENDING",
            tags=[t.tag for t in m.tags] if m.tags else [],
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


memory_service = MemoryService()
