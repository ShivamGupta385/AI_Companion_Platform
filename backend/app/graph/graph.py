from langgraph.graph import StateGraph, END, START

from backend.app.graph.state import CompanionState

from backend.app.graph.nodes.memory_node import memory_node
from backend.app.graph.nodes.history_node import history_node
from backend.app.graph.nodes.long_term_memory_node import long_term_memory_node
from backend.app.graph.nodes.document_node import document_node
from backend.app.graph.nodes.rag_node import rag_node
from backend.app.graph.nodes.graph_rag_node import graph_rag_node
from backend.app.graph.nodes.companion_node import companion_node
from backend.app.graph.nodes.llm_node import llm_node


def build_graph():
    graph_builder = StateGraph(CompanionState)

    # Nodes
    graph_builder.add_node("memory", memory_node)
    graph_builder.add_node("history", history_node)
    graph_builder.add_node("long_term_memory", long_term_memory_node)
    graph_builder.add_node("documents", document_node)
    graph_builder.add_node("rag", rag_node)
    graph_builder.add_node("graph_rag", graph_rag_node)
    graph_builder.add_node("companion", companion_node)
    graph_builder.add_node("llm", llm_node)

    # Entry Point
    graph_builder.add_edge(START, "memory")

    # Flow
    graph_builder.add_edge("memory", "history")
    graph_builder.add_edge("history", "long_term_memory")
    graph_builder.add_edge("long_term_memory", "documents")
    graph_builder.add_edge("documents", "rag")
    graph_builder.add_edge("rag", "graph_rag")
    graph_builder.add_edge("graph_rag", "companion")
    graph_builder.add_edge("companion", "llm")
    graph_builder.add_edge("llm", END)

    return graph_builder          # ← return UNCOMPILED builder


# Module-level compiled graph (no checkpointer — for simple imports)
graph = build_graph().compile()