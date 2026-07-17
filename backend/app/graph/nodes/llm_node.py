from backend.app.services.llm_provider import llm
from backend.app.utils.text_cleaner import (
    clean_text,
    clean_string_list
)
from langchain_core.messages import AIMessageChunk

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


async def llm_node(state):
    user_message = clean_text(state["user_message"])

    # --------------------------------------------------
    # 1) SHORT-TERM MEMORY (same conversation thread)
    # --------------------------------------------------
    raw_memory = state.get("memory", []) or []
    raw_history = state.get("history", []) or []

    memory = [
        (role, clean_text(text))
        for role, text in raw_memory
    ]

    history = [
        (role, clean_text(text))
        for role, text in raw_history
    ]

    # --------------------------------------------------
    # 2) LONG-TERM MEMORY (cross-conversation)
    # --------------------------------------------------
    long_term_memories = clean_string_list(
        state.get("long_term_memories", [])
    )

    conversation_summaries = clean_string_list(
        state.get("conversation_summaries", [])
    )

    # --------------------------------------------------
    # 3) CROSS-AGENT MEMORY (from other companions)
    # --------------------------------------------------
    cross_agent_context = clean_text(
        state.get("cross_agent_context", "")
    )
    has_cross_agent_memory = bool(
        cross_agent_context and cross_agent_context.strip()
    )

    # --------------------------------------------------
    # 4) DOCUMENT RAG
    # --------------------------------------------------
    documents = clean_string_list(
        state.get("document_names", [])
    )

    latest_document_name = clean_text(
        state.get("latest_document_name")
    )
    latest_document_id = state.get("latest_document_id")
    retrieved_context = clean_text(
        state.get("retrieved_context", "")
    )

    # --------------------------------------------------
    # 5) GRAPH RAG
    # --------------------------------------------------
    graph_context = clean_text(
        state.get("graph_context", "")
    )

    # --------------------------------------------------
    # 6) QUERY TYPE / MEMORY STATUS
    # --------------------------------------------------
    memory_query = is_memory_query(user_message)
    document_query = is_document_query(user_message)

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

    cross_agent_memory_status = (
        "Cross-companion intelligence from other agents is available."
        if has_cross_agent_memory
        else "No cross-companion intelligence available yet."
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
    # 7) HARD GUARDRAILS FOR DOCUMENT QUERIES
    # --------------------------------------------------
    if document_query and not has_any_document:
        return {
            **state,
            "response": (
                "I don't see any uploaded documents in your account yet. "
                "Please upload a PDF, TXT, or DOCX file and I can summarize or explain it for you."
            )
        }

    if document_query and has_latest_document and not has_retrieved_context:
        return {
            **state,
            "response": (
                f"I found your latest uploaded document {latest_document_name}, "
                f"but I couldn't extract meaningful text from it for summarization. "
                f"This usually happens when the PDF is image-based, scanned, or contains little/no selectable text. "
                f"If you want, I can help you improve the ingestion pipeline with OCR fallback so these files can also be summarized."
            )
        }

    # --------------------------------------------------
    # 7.5) CRITICAL SUMMARY STATUS FOR MEMORY LEAK FIX
    # --------------------------------------------------
    if conversation_summaries:
        summary_status_text = "YES, you have spoken to this user in previous chats. The summaries below PROVE that past discussions happened. NEVER say 'this is our first conversation', 'I don't see anything earlier', or 'I don't have any saved conversations'. Instead, say 'Yes, in our previous chats we discussed...' and weave in the facts from the summaries naturally."
    else:
        summary_status_text = "No past conversation summaries exist. This truly is the first time you are speaking to this user."

    # --------------------------------------------------
    # 8) SYSTEM PROMPT (REMOVED {memory} FROM TEXT)
    # --------------------------------------------------
    system_prompt = clean_text(f"""
{state.get('system_prompt', '')}

THREAD MEMORY STATUS:
{thread_memory_status}

LONG-TERM USER MEMORY:
{long_term_memories}

PAST CONVERSATION SUMMARIES STATUS:
{summary_status_text}

PAST CONVERSATION SUMMARIES:
{conversation_summaries}

LONG-TERM MEMORY STATUS:
{long_term_memory_status}

CROSS-COMPANION INTELLIGENCE:
{cross_agent_context if has_cross_agent_memory else "No cross-companion intelligence available for this query."}

CROSS-COMPANION MEMORY STATUS:
{cross_agent_memory_status}

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

1. You have access to FIVE kinds of context:
   A) THREAD CONVERSATION MEMORY = messages from the current conversation thread
   B) LONG-TERM USER MEMORY = durable memories collected from older conversations
   C) PAST CONVERSATION SUMMARIES = summaries of previous chat threads
   D) GRAPH KNOWLEDGE CONTEXT = structured entity/relationship knowledge extracted from user documents or memory
   E) CROSS-COMPANION INTELLIGENCE = context gathered from other AGIX companions about this user

2. Use THREAD CONVERSATION MEMORY first for follow-up questions inside the current chat.

3. Use LONG-TERM USER MEMORY and PAST CONVERSATION SUMMARIES when the user asks about things discussed in older conversations or asks for remembered personal/project context across chats.

4. Use GRAPH KNOWLEDGE CONTEXT when the user asks about:
   - relationships between technologies, tools, projects, concepts, or entities
   - structured facts extracted from uploaded documents
   - project architecture, dependencies, integrations, or related concepts

5. If the user asks a memory-related question and meaningful thread memory exists, answer from the current thread memory first.

6. If the user asks a memory-related question but there is no meaningful thread memory in the current chat, check LONG-TERM USER MEMORY and PAST CONVERSATION SUMMARIES before saying you don't know.

7. EXHAUSTIVE RECALL: When asked about past discussions, scan the LONG-TERM USER MEMORY and PAST CONVERSATION SUMMARIES comprehensively. Mention all relevant specific details (such as specific topics, project names, book titles, technical concepts, or personal preferences) found in the text. Avoid giving a vague, high-level summary when specific data points are available in the context.
   Example BAD: "We discussed your work."
   Example GOOD: "We discussed your work, specifically the client onboarding process, the new CRM software integration, and the upcoming team workshop."

8. CRITICAL MEMORY RULE: If the user asks "do you remember", "what did we discuss", or similar:
   - Look at PAST CONVERSATION SUMMARIES STATUS. If it says "YES, you have spoken...", you MUST acknowledge past chats. Say "Yes, we've discussed..." and list the facts from the summaries.
   - ONLY say "I don't see that in our current chat or saved conversation memory yet" if BOTH the LONG-TERM USER MEMORY list AND the PAST CONVERSATION SUMMARIES list are completely empty.
   - NEVER say "This is our first conversation" if summaries or long-term memories are present.

9. Do NOT invent previous discussion details.

10. Do NOT say "I don't have access to previous conversations" if long-term memory or summaries are available.

11. AVAILABLE DOCUMENTS are the user's uploaded files.

12. RETRIEVED DOCUMENT CONTEXT comes from those uploaded files.

13. If the user asks about uploaded files, use AVAILABLE DOCUMENTS.
    CRITICAL: Do NOT guess what a user is reading, learning, or working on based solely on a file name in the AVAILABLE DOCUMENTS list. 
    If LONG-TERM USER MEMORY explicitly states they are reading "Book A", you MUST say "Book A". Do NOT guess "Book B" just because "Book B.pdf" is sitting in the AVAILABLE DOCUMENTS list. Trust explicit memories over guessing from file names.

14. If the user asks to summarize, analyze, explain, extract, or answer from an uploaded file, use RETRIEVED DOCUMENT CONTEXT.
    - However, if the user asks "what did we discuss about [Document Name]", this is a MEMORY question. Answer what was discussed based on PAST CONVERSATION SUMMARIES.
    - If the user asks "what is actually inside [Document Name]" or "tell me about my resume", this is a DOCUMENT question. If RETRIEVED DOCUMENT CONTEXT is empty, say: "I remember we discussed this document, but I don't have the file text loaded in this current view to read the exact details."
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

17. UNIVERSAL DOCUMENT EXTRACTION RULE:
    For ANY document-related question, ALWAYS prioritize RETRIEVED DOCUMENT CONTEXT over your general knowledge.
    - Extract and present the ACTUAL CONTENT from the text provided, not just section headers or a table of contents.
    - Be highly specific and detailed — do not be vague.
    - Adapt your extraction based on the document type provided in the context (e.g., if it's a resume, extract skills/experience; if it's a research paper, extract methodology/results; if it's code, extract functions/logic).
    - Example BAD: "The document has an Education section and a Skills section."
    - Example GOOD: "The document states the candidate holds a Bachelor's degree in Computer Science with a 3.9 GPA, and is proficient in Python, AWS, and Docker."
    - Always prefer specific factual data extracted from the text over generic descriptions.

18. For graph / relationship / architecture / technology questions:
    prioritize GRAPH KNOWLEDGE CONTEXT when relevant.

19. If both RETRIEVED DOCUMENT CONTEXT and GRAPH KNOWLEDGE CONTEXT are relevant, combine them naturally in one coherent answer.

20. Maintain continuity with:
    - the companion persona
    - the user's onboarding profile
    - remembered project context
    - long-term memory

21. DOCUMENT REFERENCE RULE:
    If the user says things like "attached document", "uploaded document", "this document", or "this pdf", interpret that as the LATEST UPLOADED DOCUMENT when LATEST UPLOADED DOCUMENT NAME is available.

22. If AVAILABLE DOCUMENTS is not empty, NEVER say that the user has not uploaded any document.

23. STRICT CONTEXT ADHERENCE:
    If RETRIEVED DOCUMENT CONTEXT is present, answer directly from it.
    - Do NOT just list what sections the document has.
    - Extract the underlying factual data from those sections.
    - CRITICAL: If RETRIEVED DOCUMENT CONTEXT is EMPTY, do NOT guess or hallucinate what is inside the document. 
    - If you know a document was discussed (from memory) but the text is not provided below, say: "I remember we looked at that file in a previous chat, but I don't have the document text loaded right now to give you the specific details."
24. If the user asks to summarize or explain the attached/uploaded/latest document, assume they mean the latest uploaded document unless they explicitly name another file.

25. If RETRIEVED DOCUMENT CONTEXT clearly comes from a document, summarize that document instead of asking the user to upload again.

26. Never say "there is no document attached" if:
    - AVAILABLE DOCUMENTS is not empty
    OR
    - LATEST UPLOADED DOCUMENT NAME exists
    OR
    - RETRIEVED DOCUMENT CONTEXT exists.

27. When answering from document context, mention the document name naturally if available.

28. If CROSS-COMPANION INTELLIGENCE is available, use it to personalize your response.
    - Weave the insights naturally — do NOT reference other companions by name.
    - Example: Say "I noticed you've been sleeping poorly" NOT "Noor told me you slept 4 hours."
    - Example: Say "Given your upcoming interview" NOT "Victor mentioned you have an interview."
    - NEVER break the fourth wall about the companion system.

29. Use CROSS-COMPANION INTELLIGENCE to make smarter decisions:
    - If sleep data shows poor rest, reduce intensity (for fitness/study).
    - If stress data shows high anxiety, add calming elements.
    - If business pressure is high, acknowledge time constraints.

30. Do NOT ignore CROSS-COMPANION INTELLIGENCE when it's available. It represents real knowledge about the user from specialized agents.

31. If CROSS-COMPANION INTELLIGENCE contradicts what the user is telling you in the current conversation, trust the CURRENT conversation — the user's latest words take priority.

32. Do NOT fabricate cross-companion intelligence. Only use what is provided in the CROSS-COMPANION INTELLIGENCE section above.

33. CROSS-COMPANION INTELLIGENCE is a complementary signal, not a replacement for direct conversation. Use it to add depth, not to override what the user is saying right now.
"""
    )
    # --------------------------------------------------
    # 9) BUILD FINAL MESSAGE LIST (REMOVED DUPLICATE USER MESSAGE)
    # --------------------------------------------------
    messages = [("system", system_prompt)]

    # Remove the last message from memory if it's the current user message to avoid duplicates
    if memory and memory[-1][1] == user_message:
        memory = memory[:-1]

    if memory:
        messages.extend(memory)

    if history:
        messages.extend(history)

    messages.append(("human", user_message))

    # --------------------------------------------------
    # 10) DEBUG LOGS
    # --------------------------------------------------
    print("=" * 60)
    print("[LLM NODE] conversation_id:", state.get("conversation_id"))
    print("[LLM NODE] companion_id:", state.get("companion_id"))
    print("[LLM NODE] companion_name:", state.get("companion_name"))
    print("[LLM NODE] user_message:", user_message)
    print("[LLM LOG] memory_query:", memory_query)
    print("[LLM NODE] document_query:", document_query)
    print("[LLM NODE] thread memory messages:", len(memory))
    print("[LLM NODE] has_meaningful_thread_memory:", has_meaningful_thread_memory)
    print("[LLM NODE] long_term_memories:", len(long_term_memories))
    print("[LLM NODE] conversation_summaries:", len(conversation_summaries))
    print("[LLM NODE] has_cross_agent_memory:", has_cross_agent_memory)
    print("[LLM NODE] documents:", documents)
    print("[LLM NODE] latest_document_name:", latest_document_name)
    print("[LLM NODE] latest_document_id:", latest_document_id)
    print("[LLM NODE] retrieved_context length:", len(retrieved_context))
    print("[LLM NODE] graph_context length:", len(graph_context))
    print("=" * 60)

    # --------------------------------------------------
    # 11) LLM INVOCATION
    # --------------------------------------------------
    response_text = ""

    async for chunk in llm.astream(messages):

        if not isinstance(chunk, AIMessageChunk):
            continue

        content = chunk.content

        if isinstance(content, str):
            token = content

        elif isinstance(content, list):
            token = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
            )

        else:
            token = ""

        if token:
            token = token.replace("\x00", "")
            response_text += token

    response_text = clean_text(response_text)

    print("[LLM NODE RESPONSE]")
    print(response_text)

    return {
        **state,
        "response": response_text
    }