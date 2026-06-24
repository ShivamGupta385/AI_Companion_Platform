def history_node(state):
    """
    Same-thread history placeholder node.

    Current AGIX behavior:
    - Recent short-term thread memory is already injected from chat.py
      and passed through memory_node as state["memory"].
    - Cross-conversation summaries / durable memory are loaded separately
      in long_term_memory_node.

    So this node currently acts as a lightweight pass-through for
    optional historical context stored in state["history"].

    Future use cases for this node:
    1. summarized older messages from the same thread
    2. archived same-thread history beyond the memory buffer
    3. compression of long chat sessions before LLM invocation
    4. retrieval of older same-thread context from conversation summaries
    """

    history = state.get("history", [])

    if history is None:
        history = []

    print("=" * 60)
    print("[HISTORY NODE]")
    print("HISTORY MESSAGE COUNT:", len(history))
    print("=" * 60)

    return {
        **state,
        "history": history
    }