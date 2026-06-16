from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.config import settings
from typing import Optional


class QdrantService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        return self._client

    @property
    def collection_name(self) -> str:
        return settings.qdrant_collection_name

    async def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]
        if self.collection_name not in names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=1536,
                    distance=qmodels.Distance.COSINE,
                ),
            )

    def upsert_vectors(
        self,
        points: list[dict],
    ) -> None:
        qpoints = [
            qmodels.PointStruct(
                id=p["id"],
                vector=p["vector"],
                payload=p.get("payload", {}),
            )
            for p in points
        ]
        self.client.upsert(collection_name=self.collection_name, points=qpoints)

    def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
    ) -> list[dict]:
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
        )
        return [
            {"id": r.id, "score": r.score, "payload": r.payload}
            for r in results
        ]

    def delete_vectors(self, ids: list[str]) -> None:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qmodels.PointIdsList(points=ids),
        )

    def close(self) -> None:
        if self._client is not None:
            self.client.close()
            self._client = None


qdrant_service = QdrantService()
