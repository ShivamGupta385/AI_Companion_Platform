import asyncio
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="c:\\Users\\shiva\\ai-companion-platform\\.env")

from backend.app.services.retriever_service import retrieve_context

async def test_rag():
    print("Testing RAG retrieval...")
    try:
        results = await retrieve_context(
            user_id="test_user",
            query="debugging"
        )
        print("Results:")
        print(results)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_rag())
