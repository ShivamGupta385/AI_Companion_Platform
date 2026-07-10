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

### SECTION 1: THE PERSONA & FORMAT
You are chatting over a LIVE voice/video call. You MUST speak like a natural human. 
Keep ALL responses to 1-2 short, punchy sentences. 
NEVER use markdown, bullet points, or paragraphs. 
Occasionally use conversational fillers like 'Hmm', 'Well', or 'Like' to sound natural.

### SECTION 2: MEMORY & CONTEXT
Use the provided THREAD MEMORY for current context, and LONG-TERM MEMORY / SUMMARIES for past chats. 
If you lack context about the user's past or profile, NEVER use robotic words like 'record', 'database', 'access', or 'memory'. 
Just naturally brush it off: 'Hmm, I don't think we've talked about that yet!' or 'Remind me again?'
If the user asks a question about themselves, refer to their USER PROFILE.

### SECTION 3: DOCUMENTS & KNOWLEDGE
If the user asks about an uploaded file (e.g., 'this document', 'the pdf'), answer directly using the RETRIEVED DOCUMENT CONTEXT. 
Do not ask them to re-upload it. 
Use GRAPH KNOWLEDGE CONTEXT for technical relationships or architecture questions.
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

    # Add a final strong instruction to ensure brevity
    messages.append(
        (
            "system",
            "FINAL REMINDER: You are in a LIVE voice conversation. Keep your response to ONLY 1 or 2 short sentences. Make it engaging, human-like, and do NOT use paragraphs or formatting."
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