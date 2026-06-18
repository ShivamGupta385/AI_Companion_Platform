from backend.app.services.retriever_service import (
    retrieve_context
)

result = retrieve_context(
    "What is Python?"
)

print(result)