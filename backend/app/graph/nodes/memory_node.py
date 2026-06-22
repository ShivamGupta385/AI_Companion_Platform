def memory_node(state):
    """
    Memory is already injected from chat.py using the same DB session.
    So this node just passes it through.
    """
    print(f"[MEMORY NODE] Loaded {len(state.get('memory', []))} recent messages")
    return state