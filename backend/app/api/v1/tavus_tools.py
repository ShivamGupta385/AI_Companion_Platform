import json
import psycopg
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel

from backend.app.core.config import settings

router = APIRouter()

def run_postgres_query(sql: str) -> str:
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        return "Error: Only SELECT queries are allowed for safety."
        
    forbidden_tokens = ["PASSWORD_HASH", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT"]
    import re
    for token in forbidden_tokens:
        if re.search(rf'\b{token}\b', sql_upper):
            return f"Error: Access denied. SQL contains forbidden term '{token}'."

    try:
        clean_url = settings.DATABASE_URL.replace("+psycopg", "").replace("+asyncpg", "")
        with psycopg.connect(clean_url) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                if cur.description is None:
                    return "Query executed successfully, but returned no rows."
                col_names = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                result = [dict(zip(col_names, row)) for row in rows]
                
                def serialize_item(val):
                    import datetime
                    import uuid
                    if isinstance(val, (datetime.date, datetime.datetime, uuid.UUID)):
                        return str(val)
                    return val

                cleaned_result = [
                    {k: serialize_item(v) for k, v in row.items()}
                    for row in result
                ]
                return json.dumps(cleaned_result) if cleaned_result else "No results found."
    except Exception as e:
        return f"Database error: {str(e)}"

def extract_args(payload: dict) -> dict:
    """Safely extract arguments whether Tavus sends them flat or wrapped in a tool_call object."""
    if "arguments" in payload:
        args = payload["arguments"]
        if isinstance(args, str):
            try:
                return json.loads(args)
            except:
                return {}
        return args
    if "function" in payload and "arguments" in payload["function"]:
        args = payload["function"]["arguments"]
        if isinstance(args, str):
            try:
                return json.loads(args)
            except:
                return {}
        return args
    # Assume flat
    return payload

@router.post("/query_database")
async def query_database(request: Request):
    """Webhook for Tavus to run SELECT queries."""
    # 1. Basic security (Tavus sends Bearer token)
    auth = request.headers.get("Authorization")
    if auth != f"Bearer {settings.SECRET_KEY}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    body = await request.json()
    args = extract_args(body)
    
    sql = args.get("sql", "")
    if not sql:
        return {"result": "Error: No SQL provided."}
        
    result = run_postgres_query(sql)
    return {"result": result}

@router.post("/search_documents")
async def search_documents(request: Request):
    """Webhook for Tavus to search RAG documents."""
    auth = request.headers.get("Authorization")
    if auth != f"Bearer {settings.SECRET_KEY}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    body = await request.json()
    args = extract_args(body)
    
    query = args.get("query", "")
    user_id = args.get("user_id", "")
    
    if not query or not user_id:
        return {"result": "Error: query and user_id are required."}
        
    try:
        from backend.app.services.retriever_service import retrieve_context
        context = retrieve_context(query, user_id)
        if not context or not context.strip():
            return {"result": "No relevant information found in the user's documents."}
        return {"result": context}
    except Exception as e:
        return {"result": f"Error searching documents: {str(e)}"}


