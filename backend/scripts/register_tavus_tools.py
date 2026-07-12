import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

if not TAVUS_API_KEY or not BACKEND_PUBLIC_URL or not SECRET_KEY:
    print("Error: Missing TAVUS_API_KEY, BACKEND_PUBLIC_URL, or SECRET_KEY in .env")
    exit(1)

TAVUS_API_URL = "https://tavusapi.com/v2/tools"

HEADERS = {
    "x-api-key": TAVUS_API_KEY,
    "Content-Type": "application/json"
}

def register_tool(payload):
    print(f"Registering tool: {payload['name']}...")
    try:
        # First, try to find if it already exists to avoid duplicates
        res = requests.get(TAVUS_API_URL, headers=HEADERS)
        if res.status_code == 200:
            tools = res.json().get("data", [])
            for t in tools:
                if t.get("name") == payload["name"]:
                    print(f"Tool {payload['name']} already exists with ID: {t.get('tool_id')}")
                    # Update it
                    update_res = requests.patch(f"{TAVUS_API_URL}/{t.get('tool_id')}", headers=HEADERS, json=payload)
                    print(f"Updated tool {payload['name']} status:", update_res.status_code)
                    return t.get('tool_id')
    except Exception as e:
        pass

    response = requests.post(TAVUS_API_URL, headers=HEADERS, json=payload)
    if response.status_code in [200, 201]:
        tool_id = response.json().get("tool_id")
        print(f"Successfully registered {payload['name']} -> ID: {tool_id}")
        return tool_id
    else:
        print(f"Failed to register {payload['name']}. Status: {response.status_code}, Error: {response.text}")
        return None

def main():
    tools = [
        {
            "name": "query_database",
            "description": "Execute a read-only SELECT query on the user's Postgres database to look up information. NEVER select 'password_hash'.",
            "trigger_type": "in_call",
            "origin": "llm",
            "on_call": "generate_filler",
            "on_resolve": "generate_response",
            "delivery": {
                "app_message": False,
                "api": {
                    "url": f"{BACKEND_PUBLIC_URL}/tavus_tools/query_database",
                    "method": "POST",
                    "timeout": 20,
                    "auth": {
                        "type": "bearer",
                        "token": SECRET_KEY
                    },
                    "body_template": {
                        "user_id": "{user_id}",
                        "sql": "{sql}"
                    }
                }
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The exact user UUID injected via conversational_context. MUST be provided."
                    },
                    "sql": {
                        "type": "string",
                        "description": "The SQL SELECT query to run, e.g. SELECT full_name, email FROM users WHERE id = 'user_id'"
                    }
                },
                "required": ["user_id", "sql"]
            }
        },
        {
            "name": "search_documents",
            "description": "Perform a semantic search over the user's uploaded documents and notes to find relevant academic content. Pass core semantic keywords.",
            "trigger_type": "in_call",
            "origin": "llm",
            "on_call": "generate_filler",
            "on_resolve": "generate_response",
            "delivery": {
                "app_message": False,
                "api": {
                    "url": f"{BACKEND_PUBLIC_URL}/tavus_tools/search_documents",
                    "method": "POST",
                    "timeout": 20,
                    "auth": {
                        "type": "bearer",
                        "token": SECRET_KEY
                    },
                    "body_template": {
                        "user_id": "{user_id}",
                        "query": "{query}"
                    }
                }
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The exact user UUID injected via conversational_context. MUST be provided."
                    },
                    "query": {
                        "type": "string",
                        "description": "The semantic keywords to search for in the documents."
                    }
                },
                "required": ["user_id", "query"]
            }
        }
    ]

    for tool in tools:
        register_tool(tool)

if __name__ == "__main__":
    main()
