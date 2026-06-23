from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.config import settings


class ExtractedEntity(BaseModel):
    name: str = Field(description="实体名称")
    type: str = Field(description="实体类型：PERSON/PLACE/ORG/EVENT/TOPIC/TECHNOLOGY/OTHER")


class EntityExtractionResult(BaseModel):
    entities: list[ExtractedEntity] = Field(description="提取的实体列表")
    sentiment: str = Field(description="情感：POSITIVE/NEGATIVE/NEUTRAL")
    tags: list[str] = Field(description="关键词标签")


class LLMService:
    def __init__(self):
        self._llm = None
        self._embeddings = None
        self._extractor = None

    @property
    def model(self) -> str:
        return settings.openai_model

    @property
    def llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model=self.model,
                temperature=0.3,
            )
        return self._llm

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                api_key=settings.openai_api_key,
                model="text-embedding-3-small",
            )
        return self._embeddings

    @property
    def extractor(self):
        if self._extractor is None:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个实体识别助手。从文本中提取命名实体、分析情感、生成关键词标签。"),
                ("human", "{text}"),
            ])
            self._extractor = prompt | self.llm.with_structured_output(EntityExtractionResult)
        return self._extractor

    async def generate_embedding(self, text: str) -> list[float]:
        result = await self.embeddings.aembed_query(text)
        return result

    async def chat(self, messages: list[dict], **kwargs) -> str:
        result = await self.llm.ainvoke(
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
