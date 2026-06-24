from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.config import settings
from typing import Optional


class ExtractedEntity(BaseModel):
    name: str = Field(description="实体名称")
    type: str = Field(description="实体类型：PERSON/PLACE/ORG/EVENT/TOPIC/TECHNOLOGY/OTHER")


class EntityExtractionResult(BaseModel):
    entities: list[ExtractedEntity] = Field(description="提取的实体列表")
    sentiment: str = Field(description="情感：POSITIVE/NEGATIVE/NEUTRAL")
    tags: list[str] = Field(description="关键词标签")


PROVIDER_DEFAULTS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
    },
}


class LLMService:
    def __init__(self):
        self._llm = None
        self._embeddings = None
        self._extractor = None
        self._active_key: Optional[str] = None

    @property
    def api_key(self) -> str:
        return self._active_key or settings.llm_api_key

    def set_api_key(self, key: Optional[str]) -> None:
        if key and key != self._active_key:
            self._active_key = key
            self._llm = None
            self._embeddings = None
            self._extractor = None

    @property
    def provider(self) -> str:
        return settings.llm_provider

    @property
    def model(self) -> str:
        provider_defaults = PROVIDER_DEFAULTS.get(self.provider, {})
        return settings.llm_model or provider_defaults.get("model", "gpt-4o-mini")

    @property
    def base_url(self) -> str:
        provider_defaults = PROVIDER_DEFAULTS.get(self.provider, {})
        return settings.llm_base_url or provider_defaults.get("base_url", "")

    def _get_proxy(self) -> str | None:
        import os
        return os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("ALL_PROXY")

    def _get_llm(self) -> ChatOpenAI:
        if self._llm is None:
            kwargs = {
                "api_key": self.api_key,
                "model": self.model,
                "temperature": 0.3,
            }
            if self.base_url:
                kwargs["base_url"] = self.base_url
            proxy = self._get_proxy()
            if proxy:
                kwargs["openai_proxy"] = proxy
            self._llm = ChatOpenAI(**kwargs)
        return self._llm

    def _get_embeddings(self) -> OpenAIEmbeddings:
        if self._embeddings is None:
            kwargs = {
                "api_key": self.api_key,
                "model": "text-embedding-3-small",
            }
            proxy = self._get_proxy()
            if proxy:
                kwargs["openai_proxy"] = proxy
            if self.base_url and self.provider != "openai":
                kwargs["base_url"] = self.base_url
            self._embeddings = OpenAIEmbeddings(**kwargs)
        return self._embeddings

    @property
    def extractor(self):
        if self._extractor is None:
            from langchain_core.output_parsers import StrOutputParser
            sys_text = (
                "你是一个实体识别助手。从文本中提取命名实体、分析情感、生成关键词标签。"
                "返回纯 JSON 格式，不要 markdown 代码块。"
                'Schema: {{"entities": [{{"name": "string", "type": "PERSON|PLACE|ORG|EVENT|TOPIC|TECHNOLOGY|OTHER"}}], '
                '"sentiment": "POSITIVE|NEGATIVE|NEUTRAL", "tags": ["string"]}}'
            )
            prompt = ChatPromptTemplate.from_messages([
                ("system", sys_text),
                ("human", "{text}"),
            ])
            self._extractor = prompt | self._get_llm() | StrOutputParser()
        return self._extractor

    async def generate_embedding(self, text: str) -> list[float]:
        import asyncio
        result = await asyncio.wait_for(
            self._get_embeddings().aembed_query(text),
            timeout=15.0,
        )
        return result

    async def chat(self, messages: list[dict], **kwargs) -> str:
        result = await self._get_llm().ainvoke(
            [{"role": m["role"], "content": m["content"]} for m in messages],
            **kwargs,
        )
        return result.content if hasattr(result, "content") else str(result)

    async def extract_entities(self, text: str) -> dict:
        import asyncio, json
        try:
            raw = await asyncio.wait_for(
                self.extractor.ainvoke({"text": text}),
                timeout=20.0,
            )
            # Clean markdown fences if present
            clean = raw.strip().strip("`").strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
            clean = clean.strip("`").strip()
            data = json.loads(clean)
            entities = data.get("entities", [])
            # Validate entity types
            valid_types = {"PERSON", "PLACE", "ORG", "EVENT", "TOPIC", "TECHNOLOGY", "OTHER"}
            for e in entities:
                if e.get("type", "").upper() not in valid_types:
                    e["type"] = "OTHER"
                else:
                    e["type"] = e["type"].upper()
            sentiment = data.get("sentiment", "NEUTRAL").upper()
            if sentiment not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
                sentiment = "NEUTRAL"
            return {
                "entities": entities,
                "sentiment": sentiment,
                "tags": data.get("tags", []),
            }
        except Exception:
            return {"entities": [], "sentiment": "NEUTRAL", "tags": []}

    async def close(self) -> None:
        self._llm = None
        self._embeddings = None
        self._extractor = None


llm_service = LLMService()