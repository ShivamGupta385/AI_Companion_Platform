from backend.app.services.llm_provider import llm


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

DOCUMENT_QUERY_KEYWORDS = [
    "attached document",
    "uploaded document",
    "this document",
    "this pdf",
    "the pdf",
    "summarize the document",
    "summarize attached document",
    "summarize uploaded document",
    "summarize the attached document",
    "what is in the attached document",
    "what is there in the attached document",
    "summarize the pdf",
    "explain the attached file",
    "list attached document",
    "list attached documents",
]


def is_memory_query(query: str) -> bool:
    query_lower = query.lower().strip()
    return any(
        keyword in query_lower
        for keyword in MEMORY_QUERY_KEYWORDS
    )


def is_document_query(query: str) -> bool:
    query_lower = query.lower().strip()
    return any(
        keyword in query_lower
        for keyword in DOCUMENT_QUERY_KEYWORDS
    )


def llm_node(state):
    user_message = state["user_message"]

    # --------------------------------------------------
    # 1) SHORT-TERM MEMORY (same conversation thread)
    # --------------------------------------------------
    memory = state.get("memory", [])
    history = state.get("history", [])

    # --------------------------------------------------
    # 2) LONG-TERM MEMORY (cross-conversation)
    # --------------------------------------------------
    long_term_memories = state.get(
        "long_term_memories",
        []
    )
    conversation_summaries = state.get(
        "conversation_summaries",
        []
    )

    # --------------------------------------------------
    # 3) DOCUMENT RAG
    # --------------------------------------------------
    documents = state.get("document_names", [])
    latest_document_name = state.get(
        "latest_document_name"
    )
    latest_document_id = state.get(
        "latest_document_id"
    )
    retrieved_context = state.get(
        "retrieved_context",
        ""
    )

    # --------------------------------------------------
    # 4) GRAPH RAG
    # --------------------------------------------------
    graph_context = state.get(
        "graph_context",
        ""
    )

    # --------------------------------------------------
    # 5) QUERY TYPE / MEMORY STATUS
    # --------------------------------------------------
    memory_query = is_memory_query(user_message)
    document_query = is_document_query(user_message)

    # If memory only contains current user message,
    # do not pretend earlier thread context exists.
    has_meaningful_thread_memory = len(memory) >= 2

    thread_memory_status = (
        "Conversation history from this thread is available."
        if has_meaningful_thread_memory
        else "There is no meaningful earlier conversation history in this thread yet."
    )

    long_term_memory_status = (
        "Cross-conversation long-term memory is available."
        if long_term_memories or conversation_summaries
        else "No cross-conversation long-term memory is available yet."
    )

    graph_memory_status = (
        "Graph knowledge context is available."
        if graph_context
        else "No graph knowledge context is available for this query."
    )

    has_any_document = bool(documents)
    has_latest_document = bool(latest_document_name)
    has_retrieved_context = bool(
        retrieved_context and retrieved_context.strip()
    )

    # --------------------------------------------------
    # 6) HARD GUARDRAILS FOR DOCUMENT QUERIES
    # --------------------------------------------------
    # Case A:
    # User is asking about attached/uploaded document
    # but user has no uploaded docs at all
    if document_query and not has_any_document:
        return {
            **state,
            "response": (
                "I don't see any uploaded documents in your account yet. "
                "Please upload a PDF, TXT, or DOCX file and I can summarize or explain it for you."
            )
        }

    # Case B:
    # Latest document exists but retrieval returned nothing.
    # This usually means the file was uploaded but text extraction failed,
    # or the PDF is scanned / image-based / empty.
    if document_query and has_latest_document and not has_retrieved_context:
        return {
            **state,
            "response": (
                f"I found your latest uploaded document **{latest_document_name}**, "
                f"but I couldn't extract meaningful text from it for summarization. "
                f"This usually happens when the PDF is image-based, scanned, or contains little/no selectable text. "
                f"If you want, I can help you improve the ingestion pipeline with OCR fallback so these files can also be summarized."
            )
        }

    # --------------------------------------------------
    # 7) SYSTEM PROMPT
    # --------------------------------------------------
    system_prompt = f"""
{state.get('system_prompt', '')}

USER PROFILE:
{state.get('user_profile', {})}

THREAD CONVERSATION MEMORY:
{memory}

THREAD MEMORY STATUS:
{thread_memory_status}

LONG-TERM USER MEMORY:
{long_term_memories}

PAST CONVERSATION SUMMARIES:
{conversation_summaries}

LONG-TERM MEMORY STATUS:
{long_term_memory_status}

AVAILABLE DOCUMENTS:
{documents}

LATEST UPLOADED DOCUMENT NAME:
{latest_document_name}

LATEST UPLOADED DOCUMENT ID:
{latest_document_id}

RETRIEVED DOCUMENT CONTEXT:
{retrieved_context}

GRAPH KNOWLEDGE CONTEXT:
{graph_context}

GRAPH MEMORY STATUS:
{graph_memory_status}

IMPORTANT INSTRUCTIONS:

1. You have access to FOUR kinds of context:
   A) THREAD CONVERSATION MEMORY = messages from the current conversation thread
   B) LONG-TERM USER MEMORY = durable memories collected from older conversations
   C) PAST CONVERSATION SUMMARIES = summaries of previous chat threads
   D) GRAPH KNOWLEDGE CONTEXT = structured entity/relationship knowledge extracted from user documents or memory

2. Use THREAD CONVERSATION MEMORY first for follow-up questions inside the current chat.

3. Use LONG-TERM USER MEMORY and PAST CONVERSATION SUMMARIES when the user asks about things discussed in older conversations or asks for remembered personal/project context across chats.

4. Use GRAPH KNOWLEDGE CONTEXT when the user asks about:
   - relationships between technologies, tools, projects, concepts, or entities
   - structured facts extracted from uploaded documents
   - project architecture, dependencies, integrations, or related concepts

5. If the user asks a memory-related question and meaningful thread memory exists, answer from the current thread memory first.

6. If the user asks a memory-related question but there is no meaningful thread memory in the current chat, check LONG-TERM USER MEMORY and PAST CONVERSATION SUMMARIES before saying you don't know.

7. If relevant information exists in LONG-TERM USER MEMORY or PAST CONVERSATION SUMMARIES, use it naturally.
   Example:
   - "You're working on the AGIX internship project."
   - "Earlier we discussed FastAPI, LangGraph, and conversation memory."

8. If the user asks a memory-related question and there is no relevant information in:
   - current thread memory
   - long-term memory
   - conversation summaries
   then say that naturally.
   Example:
   - "I don't see that in our current chat or saved conversation memory yet."

9. Do NOT invent previous discussion details.

10. Do NOT say "I don't have access to previous conversations" if long-term memory or summaries are available.

11. AVAILABLE DOCUMENTS are the user's uploaded files.

12. RETRIEVED DOCUMENT CONTEXT comes from those uploaded files.

13. If the user asks about uploaded files, use AVAILABLE DOCUMENTS.

14. If the user asks to summarize, analyze, explain, extract, or answer from an uploaded file, use RETRIEVED DOCUMENT CONTEXT.

15. If GRAPH KNOWLEDGE CONTEXT is available and relevant, use it for:
    - technology relationships
    - project architecture
    - tool dependencies
    - structured project facts
    - connected concepts from uploaded documents

16. For memory-related questions, priority order should be:
    (1) current thread memory
    (2) long-term user memory
    (3) past conversation summaries

17. For document-related questions:
    prioritize RETRIEVED DOCUMENT CONTEXT over general knowledge.

18. For graph / relationship / architecture / technology questions:
    prioritize GRAPH KNOWLEDGE CONTEXT when relevant.

19. If both RETRIEVED DOCUMENT CONTEXT and GRAPH KNOWLEDGE CONTEXT are relevant,
    combine them naturally in one coherent answer.

20. Maintain continuity with:
    - the companion persona
    - the user's onboarding profile
    - remembered project context
    - long-term memory

21. IMPORTANT:
    If the user says things like:
    - "attached document"
    - "uploaded document"
    - "this document"
    - "this pdf"
    then interpret that as the LATEST UPLOADED DOCUMENT when LATEST UPLOADED DOCUMENT NAME is available.

22. If AVAILABLE DOCUMENTS is not empty, NEVER say that the user has not uploaded any document.

23. If RETRIEVED DOCUMENT CONTEXT is present, answer from it directly.

24. If the user asks to summarize or explain the attached/uploaded/latest document:
    - assume they mean the latest uploaded document unless they explicitly name another file.

25. If RETRIEVED DOCUMENT CONTEXT clearly comes from a document, summarize that document instead of asking the user to upload again.

26. Never say "there is no document attached" if:
    - AVAILABLE DOCUMENTS is not empty
    OR
    - LATEST UPLOADED DOCUMENT NAME exists
    OR
    - RETRIEVED DOCUMENT CONTEXT exists.

27. When answering from document context, mention the document name naturally if available.
"""

    # --------------------------------------------------
    # 8) BUILD FINAL MESSAGE LIST
    # --------------------------------------------------
    messages = [("system", system_prompt)]

    # Add short-term thread memory
    if memory:
        messages.extend(memory)

    # Add optional history
    if history:
        messages.extend(history)

    # Add current user message
    messages.append(
        (
            "human",
            user_message
        )
    )

    # --------------------------------------------------
    # 9) DEBUG LOGS
    # --------------------------------------------------
    print("=" * 60)
    print("[LLM NODE] conversation_id:", state.get("conversation_id"))
    print("[LLM NODE] companion_id:", state.get("companion_id"))
    print("[LLM NODE] user_message:", user_message)
    print("[LLM NODE] memory_query:", memory_query)
    print("[LLM NODE] document_query:", document_query)
    print("[LLM NODE] thread memory messages:", len(memory))
    print("[LLM NODE] has_meaningful_thread_memory:", has_meaningful_thread_memory)
    print("[LLM NODE] long_term_memories:", len(long_term_memories))
    print("[LLM NODE] conversation_summaries:", len(conversation_summaries))
    print("[LLM NODE] documents:", documents)
    print("[LLM NODE] latest_document_name:", latest_document_name)
    print("[LLM NODE] latest_document_id:", latest_document_id)
    print("[LLM NODE] retrieved_context length:", len(retrieved_context))
    print("[LLM NODE] graph_context length:", len(graph_context))
    print("=" * 60)

    # --------------------------------------------------
    # 10) LLM INVOCATION
    # --------------------------------------------------
    response = llm.invoke(messages)

    print("[LLM NODE RESPONSE]")
    print(response.content)

    return {
        **state,
        "response": response.content
    }