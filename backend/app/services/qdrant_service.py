"""ChromaDB 嵌入式向量存储，替代 Qdrant。

保留与原 qdrant_service 相同的方法签名，业务层无需改动。
特性：
- 本地持久化（无需独立服务）
- 支持向量插入、搜索、删除
"""
from pathlib import Path
from typing import Optional
from app.config import settings


class QdrantService:
    """ChromaDB 实现的向量服务，接口与原 Qdrant 版兼容。"""

    def __init__(self):
        self._client = None
        self._collection = None

    @property
    def _persist_dir(self) -> str:
        path = settings.chroma_persist_dir or str(Path(settings.data_dir) / "chroma")
        Path(path).mkdir(parents=True, exist_ok=True)
        return path

    @property
    def client(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=self._persist_dir)
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    @property
    def collection_name(self) -> str:
        return settings.chroma_collection_name

    async def ensure_collection(self) -> None:
        """初始化 collection（桌面端启动时调用）。"""
        # get_or_create_collection 已确保存在
        _ = self.collection

    def upsert_vectors(self, points: list[dict]) -> None:
        """插入或更新向量。

        points: [{"id": str, "vector": list[float], "payload": dict}]
        """
        if not points:
            return
        ids = [str(p["id"]) for p in points]
        vectors = [p["vector"] for p in points]
        metadatas = [p.get("payload", {}) or {} for p in points]
        # ChromaDB metadata 值必须是基础类型
        safe_metadatas = []
        for m in metadatas:
            safe = {}
            for k, v in m.items():
                if isinstance(v, (str, int, float, bool)) or v is None:
                    safe[k] = v if v is not None else ""
                else:
                    safe[k] = str(v)
            safe_metadatas.append(safe)
        self.collection.upsert(
            ids=ids,
            embeddings=vectors,
            metadatas=safe_metadatas,
        )

    def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
    ) -> list[dict]:
        """搜索最相似的向量。

        返回格式与原 Qdrant 兼容：[{"id": ..., "score": ..., "payload": ...}]
        """
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
        )
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        output = []
        for idx, _id in enumerate(ids):
            # ChromaDB cosine distance 越小越相似，转换为 0~1 的 score（1 为最相似）
            distance = distances[idx] if idx < len(distances) else 1.0
            score = 1.0 - distance
            if score_threshold is not None and score < score_threshold:
                continue
            payload = metadatas[idx] if idx < len(metadatas) else {}
            output.append({"id": _id, "score": score, "payload": payload})
        return output

    def delete_vectors(self, ids: list[str]) -> None:
        if not ids:
            return
        self.collection.delete(ids=[str(i) for i in ids])

    def close(self) -> None:
        # ChromaDB PersistentClient 无需显式关闭
        self._client = None
        self._collection = None


qdrant_service = QdrantService()
