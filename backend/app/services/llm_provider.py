from langchain_openai import ChatOpenAI
from backend.app.core.config import settings

llm = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=settings.OPENAI_API_KEY,
    temperature=0.7
)