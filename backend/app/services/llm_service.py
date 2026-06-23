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
    "openai": {
        "base_url": "",
        "model": "gpt-4o-mini",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
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

    def _get_llm(self) -> ChatOpenAI:
        if self._llm is None:
            kwargs = {
                "api_key": self.api_key,
                "model": self.model,
                "temperature": 0.3,
            }
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._llm = ChatOpenAI(**kwargs)
        return self._llm

    def _get_embeddings(self) -> OpenAIEmbeddings:
        if self._embeddings is None:
            kwargs = {
                "api_key": self.api_key,
                "model": "text-embedding-3-small",
            }
            if self.base_url and self.provider != "openai":
                kwargs["base_url"] = self.base_url
            self._embeddings = OpenAIEmbeddings(**kwargs)
        return self._embeddings

    @property
    def extractor(self):
        if self._extractor is None:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个实体识别助手。从文本中提取命名实体、分析情感、生成关键词标签。"),
                ("human", "{text}"),
            ])
            self._extractor = prompt | self._get_llm().with_structured_output(EntityExtractionResult)
        return self._extractor

    async def generate_embedding(self, text: str) -> list[float]:
        result = await self._get_embeddings().aembed_query(text)
        return result

    async def chat(self, messages: list[dict], **kwargs) -> str:
        result = await self._get_llm().ainvoke(
            [{"role": m["role"], "content": m["content"]} for m in messages],
            **kwargs,
        )
        return result.content if hasattr(result, "content") else str(result)

    async def extract_entities(self, text: str) -> dict:
        try:
            result: EntityExtractionResult = await self.extractor.ainvoke({"text": text})
            return {
                "entities": [{"name": e.name, "type": e.type} for e in result.entities],
                "sentiment": result.sentiment,
                "tags": result.tags,
            }
        except Exception:
            return {"entities": [], "sentiment": "NEUTRAL", "tags": []}

    async def close(self) -> None:
        self._llm = None
        self._embeddings = None
        self._extractor = None


llm_service = LLMService()