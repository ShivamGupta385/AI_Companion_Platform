from langchain_google_genai import ChatGoogleGenerativeAI
from backend.app.core.config import settings

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7
)