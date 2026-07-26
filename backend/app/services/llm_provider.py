import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

try:
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("No API Key")
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        streaming=True,
    )
except Exception:
    llm = None
