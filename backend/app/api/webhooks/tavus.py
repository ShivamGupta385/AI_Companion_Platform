from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from anthropic import Anthropic
import json
import os

router = APIRouter()
client = Anthropic()

@router.post("/v1/chat/completions")
async def tavus_mcp_brain(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    user_message = messages[-1]["content"] if messages else "Hello"

    # We use STDIO transport for the Python MCP server
    with client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": user_message}],
        tools=[
            {
                "type": "mcp_server",
                "name": "postgres_db",
                "command": "mcp-server-postgres",
                "args": ["postgresql://user:shan2508@localhost:5432/ai_companion"],
                "transport": "stdio" # <-- This is the key change for Python MCP!
            }
        ],
        system="You are a helpful AI avatar. Use the Postgres database tools to answer user questions. Keep answers concise."
    ) as stream:
        
        def event_stream():
            for text in stream.text_stream:
                chunk = {
                    "id": "chatcmpl-tavus-mcp",
                    "object": "chat.completion.chunk",
                    "choices": [{
                        "index": 0,
                        "delta": {"content": text},
                        "finish_reason": None
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
            
            yield f"data: {json.dumps({'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")