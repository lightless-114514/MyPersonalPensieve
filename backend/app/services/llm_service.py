from openai import AsyncOpenAI
from app.config import settings


class LLMService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    @property
    def model(self) -> str:
        return settings.openai_model

    async def generate_embedding(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    async def chat(self, messages: list[dict], **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    async def extract_entities(self, text: str) -> dict:
        prompt = f"""Extract named entities from the following text. Return a JSON object with:
- "entities": list of {{"name": "...", "type": "PERSON|PLACE|ORG|EVENT|TOPIC|TECHNOLOGY|OTHER"}}
- "sentiment": "POSITIVE|NEGATIVE|NEUTRAL"
- "tags": list of relevant keyword tags

Text: {text}"""
        messages = [{"role": "user", "content": prompt}]
        result = await self.chat(messages, temperature=0.3)
        import json
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"entities": [], "sentiment": "NEUTRAL", "tags": []}

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None


llm_service = LLMService()
