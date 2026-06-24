def memory_node(state):
    """
    Short-term thread memory node.

    In AGIX, recent conversation memory is already built inside chat.py
    using the same DB session (so the latest flushed user message is included)
    and injected into graph state as:

        state["memory"] = [
            ("human", "..."),
            ("assistant", "..."),
            ...
        ]

    Therefore this node does not fetch from DB again.
    It only validates / passes through the memory buffer.
    """

    memory = state.get("memory", [])

    if memory is None:
        memory = []

    print("=" * 60)
    print("[MEMORY NODE]")
    print("THREAD MEMORY COUNT:", len(memory))

    if memory:
        print("[MEMORY NODE SAMPLE]")
        for role, text in memory[-4:]:
            preview = text[:120].replace("\n", " ")
            print(f"{role}: {preview}")

    print("=" * 60)

    return {
        **state,
        "memory": memory
    }