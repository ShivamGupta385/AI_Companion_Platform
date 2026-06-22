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


def is_memory_query(query: str) -> bool:
    query_lower = query.lower().strip()
    return any(keyword in query_lower for keyword in MEMORY_QUERY_KEYWORDS)


def llm_node(state):
    user_message = state["user_message"]

    # Short-term memory (same conversation thread)
    memory = state.get("memory", [])
    history = state.get("history", [])

    # Long-term memory (cross-conversation)
    long_term_memories = state.get("long_term_memories", [])
    conversation_summaries = state.get("conversation_summaries", [])

    # Documents / RAG
    documents = state.get("document_names", [])
    retrieved_context = state.get("retrieved_context", "")

    # Query type
    memory_query = is_memory_query(user_message)

    # Meaningful thread memory:
    # If memory only contains current user message, don't pretend we know past thread context.
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

RETRIEVED DOCUMENT CONTEXT:
{retrieved_context}

IMPORTANT INSTRUCTIONS:

1. You have access to THREE kinds of context:
   A) THREAD CONVERSATION MEMORY = messages from the current conversation thread
   B) LONG-TERM USER MEMORY = durable memories collected from older conversations
   C) PAST CONVERSATION SUMMARIES = summaries of previous chat threads

2. Use THREAD CONVERSATION MEMORY first for follow-up questions inside the current chat.

3. Use LONG-TERM USER MEMORY and PAST CONVERSATION SUMMARIES when the user asks about things discussed in older conversations or asks for remembered personal/project context across chats.

4. If the user asks a memory-related question and meaningful thread memory exists, answer from the current thread memory first.

5. If the user asks a memory-related question but there is no meaningful thread memory in the current chat, check LONG-TERM USER MEMORY and PAST CONVERSATION SUMMARIES before saying you don't know.

6. If relevant information exists in LONG-TERM USER MEMORY or PAST CONVERSATION SUMMARIES, use it naturally. Examples:
   - "You're working on the AGIX internship project."
   - "Earlier we discussed FastAPI, LangGraph, and conversation memory."

7. If the user asks a memory-related question and there is no relevant information in:
   - current thread memory
   - long-term memory
   - conversation summaries
   then say that naturally.
   Example:
   - "I don't see that in our current chat or saved conversation memory yet."

8. Do NOT invent previous discussion details.

9. Do NOT say "I don't have access to previous conversations" if long-term memory or summaries are available.

10. AVAILABLE DOCUMENTS are the user's uploaded files.

11. RETRIEVED DOCUMENT CONTEXT comes from those uploaded files.

12. If the user asks about uploaded files, use AVAILABLE DOCUMENTS.

13. If the user asks to summarize, analyze, or explain uploaded files, use RETRIEVED DOCUMENT CONTEXT.

14. For memory-related questions:
    priority order should be:
    (1) current thread memory
    (2) long-term user memory
    (3) past conversation summaries

15. For document-related questions:
    prioritize retrieved document context over general knowledge.

16. Maintain continuity with the companion persona, the user's onboarding profile, and remembered project context.
"""

    messages = [("system", system_prompt)]

    # Add short-term thread memory
    if memory:
        messages.extend(memory)

    # Add optional history
    if history:
        messages.extend(history)

    # Add current user message
    messages.append(("human", user_message))

    print("=" * 60)
    print("[LLM NODE] conversation_id:", state.get("conversation_id"))
    print("[LLM NODE] companion_id:", state.get("companion_id"))
    print("[LLM NODE] user_message:", user_message)
    print("[LLM NODE] memory_query:", memory_query)
    print("[LLM NODE] thread memory messages:", len(memory))
    print("[LLM NODE] has_meaningful_thread_memory:", has_meaningful_thread_memory)
    print("[LLM NODE] long_term_memories:", len(long_term_memories))
    print("[LLM NODE] conversation_summaries:", len(conversation_summaries))
    print("[LLM NODE] documents:", documents)
    print("[LLM NODE] retrieved_context length:", len(retrieved_context))
    print("=" * 60)

    response = llm.invoke(messages)

    print("[LLM NODE RESPONSE]")
    print(response.content)

    return {
        **state,
        "response": response.content
    }