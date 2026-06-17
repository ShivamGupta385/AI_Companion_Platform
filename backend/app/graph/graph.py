from langgraph.graph import (
    StateGraph,
    END
)

from backend.app.graph.state import (
    CompanionState
)

from backend.app.graph.nodes.history_node import (
    history_node
)

from backend.app.graph.nodes.companion_node import (
    companion_node
)

from backend.app.graph.nodes.llm_node import (
    llm_node
)


graph_builder = StateGraph(
    CompanionState
)

graph_builder.add_node(
    "history",
    history_node
)

graph_builder.add_node(
    "companion",
    companion_node
)

graph_builder.add_node(
    "llm",
    llm_node
)

graph_builder.set_entry_point(
    "history"
)

graph_builder.add_edge(
    "history",
    "companion"
)

graph_builder.add_edge(
    "companion",
    "llm"
)

graph_builder.add_edge(
    "llm",
    END
)

graph = graph_builder.compile()