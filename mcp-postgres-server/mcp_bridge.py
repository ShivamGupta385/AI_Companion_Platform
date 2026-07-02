import os
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

# 1. Set the DB URL BEFORE importing the postgres server 
# (It reads this variable when it loads)
os.environ["POSTGRES_URL"] = "postgresql://user:shan2508@localhost:5432/ai_companion"

# 2. Import the Postgres MCP Server
from mcp_server_postgres import server as postgres_server

# 3. Setup the SSE transport
sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_client(request) as (read_stream, write_stream):
        await postgres_server.run(
            read_stream,
            write_stream,
            postgres_server.create_initialization_options(),
        )

# 4. Create a tiny Starlette app to serve it
app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
    ]
)