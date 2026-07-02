import os
import psycopg2
from mcp.server.fastmcp import FastMCP

# 1. Create the MCP Server instance
mcp = FastMCP("agix_postgres_db")

# 2. Your Database URL
DB_URL = "postgresql://user:shan2508@localhost:5432/ai_companion"

# 3. Define the Tool that Claude will use to query your DB
@mcp.tool()
def query_database(sql: str) -> str:
    """Execute a read-only SELECT query on the user's Postgres database. Always use this tool to look up user data."""
    
    # Safety check: Only allow SELECT statements
    if not sql.strip().upper().startswith("SELECT"):
        return "Error: For safety, only SELECT queries are allowed."
    
    try:
        # Connect and query
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(sql)
        
        # Get column names and rows
        col_names = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        
        # Format as a nice string dictionary for the LLM to read
        result = [dict(zip(col_names, row)) for row in rows]
        cur.close()
        conn.close()
        
        return str(result) if result else "No results found."
        
    except Exception as e:
        return f"Database error: {str(e)}"

# 4. Create the SSE web app (Starlette)
app = mcp.sse_app()