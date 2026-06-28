from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

from backend.app.core.config import settings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

pc = Pinecone(
    api_key=settings.PINECONE_API_KEY
)

index = pc.Index(settings.PINECONE_INDEX_NAME)

vector_store = PineconeVectorStore(
    index=index,
    embedding=embeddings
)