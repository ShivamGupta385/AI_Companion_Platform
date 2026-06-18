from pinecone import Pinecone

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from backend.app.core.config import settings


embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=settings.OPENAI_API_KEY
)

pc = Pinecone(
    api_key=settings.PINECONE_API_KEY
)

index = pc.Index(
    settings.PINECONE_INDEX_NAME
)

vector_store = PineconeVectorStore(
    index=index,
    embedding=embeddings
)