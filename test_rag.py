from backend.app.graph.graph import graph

result = graph.invoke(
    {
        "conversation_id":
        "7fe2885f-0c71-44bc-979e-dab70e40b7e3",
        "companion_name": "Max",
        "user_message": "What is Python?"
    }
)

print(result)