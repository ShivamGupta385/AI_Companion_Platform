from backend.app.services.llm_provider import llm


def llm_node(state):

    messages = [
        (
            "system",
            state["system_prompt"]
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

    response = llm.invoke(
        messages
    )

    print(response.content)

    return {
        **state,
        "response": response.content
    }