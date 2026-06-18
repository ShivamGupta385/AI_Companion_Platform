from backend.app.services.llm_provider import llm


def llm_node(state):

    retrieved_context = state.get(
        "retrieved_context",
        ""
    )

    documents = state.get(
        "document_names",
        []
    )

    messages = [
        (
            "system",
            f"""
            {state['system_prompt']}

            USER PROFILE:
            {state.get('user_profile', {})}

            AVAILABLE DOCUMENTS:
            {documents}

            RETRIEVED DOCUMENT CONTEXT:
            {retrieved_context}

            IMPORTANT INSTRUCTIONS:

            1. The document names above come from the user's uploaded documents.

            2. The retrieved document context comes from those uploaded documents.

            3. If the user asks:
               - What documents have I uploaded?
               - Show my uploaded documents
               - Tell me the document name
               - Which files do I have?

               Then use AVAILABLE DOCUMENTS.

            4. If the user asks:
               - Summarize document
               - Explain document
               - Analyze document
               - What is inside the document
               - Tell me about uploaded file

               Then use RETRIEVED DOCUMENT CONTEXT.

            5. Never say:
               - No document uploaded
               - I cannot access documents
               - Please upload a document

               if AVAILABLE DOCUMENTS or
               RETRIEVED DOCUMENT CONTEXT exists.

            6. Prioritize uploaded document information
               over general knowledge.

            7. If document content exists,
               answer directly using the content.

            8. If document names exist,
               mention them when relevant.
            """
        )
    ]

    messages.extend(
        state.get(
            "history",
            []
        )
    )

    messages.append(
        (
            "human",
            state["user_message"]
        )
    )

    print("=" * 50)
    print(
        "DOCUMENTS:",
        documents
    )
    print(
        "RETRIEVED CONTEXT LENGTH:",
        len(retrieved_context)
    )
    print("=" * 50)

    response = llm.invoke(
        messages
    )

    print(response.content)

    return {
        **state,
        "response": response.content
    }