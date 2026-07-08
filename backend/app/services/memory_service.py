import json
import math
from typing import Optional
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.session import async_session_factory
from app.models.memory import (
    Memory, MemoryTag, MemoryType, Sentiment, EntityType, BigTag,
    KnowledgeEntity, MemoryEntity, Relation, PrivacyStatus,
)
from app.schemas.memory import MemoryRequest, UpdateMemoryRequest, MemoryResponse, PagedResponse
from app.services.redis_service import redis_service
from app.services.qdrant_service import qdrant_service
from app.services.llm_service import llm_service


class MemoryService:
    async def create(self, db: AsyncSession, request: MemoryRequest) -> MemoryResponse:
        mem_type = MemoryType(request.type.upper()) if request.type else MemoryType.TEXT

        # Parse big_tag if provided
        big_tag = None
        if request.big_tag:
            try:
                big_tag = BigTag(request.big_tag.upper())
            except ValueError:
                pass

        memory = Memory(
            title=request.title,
            content=request.content,
            type=mem_type,
            source_url=request.source_url,
            file_path=request.file_path,
            file_size=request.file_size,
            mime_type=request.mime_type,
            big_tag=big_tag,
            favorite=request.favorite,
        )
        # Handle privacy_status
        if request.privacy_status:
            try:
                memory.privacy_status = PrivacyStatus(request.privacy_status.upper())
            except ValueError:
                pass
        db.add(memory)
        await db.flush()

        # Add tags - collect tag strings for the response
        tag_names = []
        for tag in request.tags or []:
            t = tag.strip()
            if not t:
                continue
            mt = MemoryTag(memory_id=memory.id, tag=t)
            db.add(mt)
            tag_names.append(t)

        await db.commit()

        # Evict cache
        await redis_service.evict_recent_memories()

        # Background: extract entities/sentiment and generate embedding
        await self._process_background(memory.id, request.content, request.title, request.type)

        # Build response
        return MemoryResponse(
            id=memory.id,
            title=memory.title,
            content=memory.content,
            type=memory.type.value if memory.type else "TEXT",
            source_url=memory.source_url,
            file_path=memory.file_path,
            file_size=memory.file_size,
            mime_type=memory.mime_type,
            sentiment=None,
            sentiment_score=memory.sentiment_score,
            processing_status=memory.processing_status.value if memory.processing_status else "PENDING",
            tags=tag_names,
            big_tag=memory.big_tag.value if memory.big_tag else None,
            favorite=memory.favorite,
            privacy_status=memory.privacy_status.value if memory.privacy_status else "ANALYZE",
            created_at=memory.created_at,
            updated_at=memory.updated_at,
        )

    async def _process_background(self, memory_id: str, content: str, title: str, mem_type: str) -> None:
        """Extract entities/sentiment and generate embedding after memory creation."""
        try:
            result = await llm_service.extract_entities(content)
            sentiment_str = result.get("sentiment", "NEUTRAL").upper()
            entities = result.get("entities", [])

            try:
                sentiment_enum = Sentiment(sentiment_str)
            except ValueError:
                sentiment_enum = Sentiment.NEUTRAL

            async with async_session_factory() as sdb:
                mem = await sdb.get(Memory, memory_id)
                if mem:
                    mem.sentiment = sentiment_enum

                entity_ids = []
                for ent in entities:
                    name = ent.get("name", "").strip()
                    etype = ent.get("type", "OTHER").strip().upper()
                    if not name:
                        continue
                    existing = await sdb.execute(
                        select(KnowledgeEntity).where(KnowledgeEntity.name == name)
                    )
                    entity = existing.scalar_one_or_none()
                    if not entity:
                        try:
                            entity = KnowledgeEntity(name=name, type=EntityType(etype))
                        except ValueError:
                            entity = KnowledgeEntity(name=name, type=EntityType.OTHER)
                        sdb.add(entity)
                        await sdb.flush()
                    entity_ids.append(entity.id)

                    sdb.add(MemoryEntity(memory_id=memory_id, entity_id=entity.id))

                for i in range(len(entity_ids) - 1):
                    sdb.add(Relation(
                        source_entity_id=entity_ids[i],
                        target_entity_id=entity_ids[i + 1],
                        relation_type="RELATED_TO",
                        memory_id=memory_id,
                    ))

                await sdb.commit()
        except Exception:
            pass

        try:
            embedding = await llm_service.generate_embedding(content)
            qdrant_service.upsert_vectors([
                {"id": memory_id, "vector": embedding, "payload": {"title": title, "type": mem_type}}
            ])
        except Exception:
            pass

    async def get_all(
        self, db: AsyncSession, page: int = 0, size: int = 20, favorite: Optional[bool] = None
    ) -> PagedResponse:
        count_query = select(func.count(Memory.id))
        if favorite is not None:
            count_query = count_query.where(Memory.favorite == favorite)
        total = (await db.execute(count_query)).scalar() or 0

        query = (
            select(Memory)
            .options(selectinload(Memory.tags))
            .order_by(desc(Memory.created_at))
            .offset(page * size)
            .limit(size)
        )
        if favorite is not None:
            query = query.where(Memory.favorite == favorite)

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

    
    async def update(self, db: AsyncSession, memory_id: str, request: UpdateMemoryRequest) -> MemoryResponse:
        query = (
            select(Memory)
            .options(selectinload(Memory.tags))
            .where(Memory.id == memory_id)
        )
        result = await db.execute(query)
        memory = result.scalar_one_or_none()
        if not memory:
            raise ValueError(f"Memory not found: {memory_id}")

        if request.title is not None:
            memory.title = request.title
        if request.content is not None:
            memory.content = request.content
        if request.type is not None:
            memory.type = MemoryType(request.type.upper())
        if request.source_url is not None:
            memory.source_url = request.source_url
        if request.favorite is not None:
            memory.favorite = request.favorite
        if request.file_path is not None:
            memory.file_path = request.file_path
        if request.file_size is not None:
            memory.file_size = request.file_size
        if request.mime_type is not None:
            memory.mime_type = request.mime_type

        if request.privacy_status is not None:
            try:
                memory.privacy_status = PrivacyStatus(request.privacy_status.upper())
            except ValueError:
                pass

        if request.big_tag is not None:
            if request.big_tag == "":
                memory.big_tag = None
            else:
                try:
                    memory.big_tag = BigTag(request.big_tag.upper())
                except ValueError:
                    pass

        if request.tags is not None:
            # Remove old tags
            new_tags = set(t.strip() for t in request.tags if t.strip())
            existing_tags = set(t.tag for t in memory.tags)
            to_remove = existing_tags - new_tags
            to_add = new_tags - existing_tags

            for t in to_remove:
                mt = next((mt for mt in memory.tags if mt.tag == t), None)
                if mt:
                    await db.delete(mt)
            for t in to_add:
                memory.tags.append(MemoryTag(memory_id=memory_id, tag=t))

        await db.commit()
        await redis_service.evict_recent_memories()

        # Refetch to get fresh state
        return await self.get_by_id(db, memory_id)

    async def delete(self, db: AsyncSession, memory_id: str) -> None:
        """删除记忆及其关联的文件。"""
        query = (
            select(Memory)
            .options(selectinload(Memory.tags))
            .where(Memory.id == memory_id)
        )
        result = await db.execute(query)
        memory = result.scalar_one_or_none()
        if not memory:
            raise ValueError(f"Memory not found: {memory_id}")

        # 删除关联文件
        if memory.file_path:
            try:
                from app.services.upload_service import delete_file
                delete_file(memory.file_path)
            except Exception:
                pass

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
            file_size=m.file_size,
            mime_type=m.mime_type,
            sentiment=m.sentiment.value if m.sentiment else None,
            sentiment_score=m.sentiment_score,
            processing_status=m.processing_status.value if m.processing_status else "PENDING",
            tags=[t.tag for t in m.tags] if m.tags else [],
            big_tag=m.big_tag.value if m.big_tag else None,
            favorite=m.favorite,
            privacy_status=m.privacy_status.value if m.privacy_status else "ANALYZE",
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


memory_service = MemoryService()
