# backend/app/graph/nodes/rag_node.py

import traceback

from backend.app.services.retriever_service import retrieve_context
from backend.app.utils.text_cleaner import clean_text


# --------------------------------------------------
# Query classification keyword lists
# --------------------------------------------------

MEMORY_QUERY_KEYWORDS = [
    "remember",
    "last conversation",
    "previous conversation",
    "previous chat",
    "earlier conversation",
    "what did we discuss",
    "what did i say",
    "what did we do",
    "continue from last time",
    "continue from previous",
    "do you remember",
    "our last chat",
    "earlier in this chat",
    "what project am i working on",
    "what am i learning",
]

IDENTITY_QUERY_KEYWORDS = [
    "do you know my name",
    "do you know who i am",
    "who am i",
    "what do you know about me",
    "what do you know about my",
    "tell me about myself",
    "what's my name",
    "what is my name",
    "my name is",
]

GREETING_KEYWORDS = [
    "hey",
    "hello",
    "hi",
    "hii",
    "good morning",
    "good evening",
    "good night",
    "how are you",
    "how's it going",
    "what's up",
    "sup",
    "yo",
    "thanks",
    "thank you",
    "bye",
    "goodbye",
    "see you",
    "okay",
    "ok",
    "cool",
    "nice",
    "great",
    "awesome",
    "sure",
    "yeah",
    "yes",
    "no",
]

COMPANION_QUERY_KEYWORDS = [
    "what can you do",
    "what do you do",
    "who are you",
    "what are you",
    "can you help",
    "i need help",
    "give me advice",
    "i feel",
    "i'm feeling",
    "i am feeling",
    "i'm stressed",
    "i am stressed",
    "i'm anxious",
    "i am anxious",
    "i can't sleep",
    "i cannot sleep",
    "i'm sad",
    "i am sad",
    "i'm worried",
    "i am worried",
    "i'm overwhelmed",
    "i am overwhelmed",
    "i'm tired",
    "i am tired",
    "i'm bored",
    "i am bored",
    "i'm lonely",
    "i am lonely",
    "i'm scared",
    "i am scared",
    "i'm angry",
    "i am angry",
    "i'm frustrated",
    "i am frustrated",
    "calm me down",
    "relax",
    "meditation",
    "breathe",
    "breathing",
    "sleep",
    "mindful",
]

DOCUMENT_QUERY_KEYWORDS = [
    "document",
    "file",
    "pdf",
    "resume",
    "paper",
    "article",
    "uploaded",
    "attached",
    "summarize",
    "summary of",
    "explain the",
    "what does the",
    "what is in the",
    "what's in the",
    "tell me about the",
    "what does it say",
    "find in the",
    "search in",
    "according to the",
    "based on the document",
    "based on the file",
    "based on the pdf",
    "based on the paper",
    "from the document",
    "from the file",
    "from the pdf",
    "from the paper",
    "the document says",
    "the file says",
    "the pdf says",
    "the paper says",
    "read the",
    "go through the",
    "analyze the",
    "review the",
    "what are my skills",
    "what are my qualifications",
    "what's my experience",
    "what is my experience",
    "my skills",
    "my qualifications",
    "my experience",
    "my projects",
    "my work history",
    "my education",
    "my tech stack",
    "my technologies",
]

LATEST_DOCUMENT_QUERIES = [
    "the uploaded document",
    "the document",
    "the file",
    "the pdf",
    "this document",
    "this file",
    "this pdf",
    "uploaded document",
    "uploaded file",
    "uploaded pdf",
    "attached document",
    "attached file",
    "attached pdf",
    "latest document",
    "latest file",
    "recent document",
    "recent file",
]


# --------------------------------------------------
# Classification functions
# --------------------------------------------------

def is_memory_query(query: str) -> bool:
    query_lower = query.lower().strip()
    return any(keyword in query_lower for keyword in MEMORY_QUERY_KEYWORDS)


def is_identity_query(query: str) -> bool:
    query_lower = query.lower().strip()
    return any(keyword in query_lower for keyword in IDENTITY_QUERY_KEYWORDS)


def is_greeting_query(query: str) -> bool:
    query_lower = query.lower().strip()
    words = query_lower.split()
    if len(words) <= 3:
        return any(keyword in query_lower for keyword in GREETING_KEYWORDS)
    if query_lower in GREETING_KEYWORDS:
        return True
    return False


def is_companion_query(query: str) -> bool:
    query_lower = query.lower().strip()
    return any(keyword in query_lower for keyword in COMPANION_QUERY_KEYWORDS)


def is_document_query(query: str) -> bool:
    query_lower = query.lower().strip()
    return any(keyword in query_lower for keyword in DOCUMENT_QUERY_KEYWORDS)


def refers_to_latest_document(query: str) -> bool:
    """
    Check if query refers to 'the' document (latest one)
    vs a specific named document.
    """
    query_lower = query.lower().strip()

    specific_file_indicators = [".pdf", ".txt", ".docx", ".doc"]

    for indicator in specific_file_indicators:
        if indicator not in query_lower:
            continue

        ext_pos = query_lower.find(indicator)
        before_ext = query_lower[:ext_pos].strip()

        if before_ext and len(before_ext.split()) >= 1:
            if before_ext not in ["the", "this", "that", "a", "an", "my"]:
                return False

    return any(phrase in query_lower for phrase in LATEST_DOCUMENT_QUERIES)


def should_skip_rag(query: str) -> bool:
    query_lower = query.lower().strip()

    if len(query_lower) < 10:
        return True

    if is_memory_query(query):
        return True

    if is_identity_query(query):
        return True

    if is_greeting_query(query):
        return True

    if is_companion_query(query):
        return True

    if not is_document_query(query):
        return True

    return False


# --------------------------------------------------
# Node
# --------------------------------------------------

async def rag_node(state):
    try:
        query = clean_text(state.get("user_message", ""))
        user_id = state.get("user_id")

        if not query or not query.strip():
            print("=" * 60)
            print("[RAG NODE] Empty query — skipping retrieval")
            print("=" * 60)

            return {
                **state,
                "retrieved_context": ""
            }

        query = query.strip()

        # --------------------------------------------------
        # Smart RAG gating
        # --------------------------------------------------
        if should_skip_rag(query):
            print("=" * 60)
            print("[RAG NODE] Skipping retrieval (non-document query)")
            print("QUERY:", query)

            if is_memory_query(query):
                print("REASON: Memory/history query")
            elif is_identity_query(query):
                print("REASON: Identity/profile query")
            elif is_greeting_query(query):
                print("REASON: Greeting/casual")
            elif is_companion_query(query):
                print("REASON: Companion/emotional query")
            elif len(query) < 10:
                print("REASON: Query too short")
            else:
                print("REASON: No document keywords detected")

            print("=" * 60)

            return {
                **state,
                "retrieved_context": ""
            }

        # --------------------------------------------------
        # Determine retrieval scope
        # --------------------------------------------------
        latest_document_id = state.get("latest_document_id")
        latest_document_name = clean_text(state.get("latest_document_name", ""))
        use_latest_only = refers_to_latest_document(query)

        print("=" * 60)
        print("[RAG NODE] Running retrieval (document query detected)")
        print("QUERY:", query)
        print("LATEST DOCUMENT:", latest_document_name)
        print("USE LATEST ONLY:", use_latest_only)

        # --------------------------------------------------
        # Call retriever with user_id + document scope
        # --------------------------------------------------
        context = await retrieve_context(
            query=query,
            user_id=user_id,
            document_id=latest_document_id if use_latest_only else None,
        )

        if context is None:
            context = ""

        context = clean_text(context)

        print("[RAG NODE] CONTEXT LENGTH:", len(context))
        print("[RAG NODE] CONTEXT PREVIEW:")
        print(context[:500] if context else "No retrieved context")
        print("=" * 60)

        return {
            **state,
            "retrieved_context": context
        }

    except Exception as e:
        print("=" * 60)
        print("[RAG NODE ERROR]")
        print("ERROR:", str(e))
        traceback.print_exc()
        print("=" * 60)
        raise