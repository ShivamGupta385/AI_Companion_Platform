import os
import re
import requests
import json
from dotenv import load_dotenv

load_dotenv()

TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")
BACKEND_PUBLIC_URL = os.getenv("BACKEND_URL", "").rstrip("/")
SECRET_KEY = os.getenv("SECRET_KEY")

if not TAVUS_API_KEY or not BACKEND_PUBLIC_URL or not SECRET_KEY:
    print("Error: Missing TAVUS_API_KEY, BACKEND_URL, or SECRET_KEY in .env")
    exit(1)

HEADERS = {
    "x-api-key": TAVUS_API_KEY,
    "Content-Type": "application/json"
}

def register_tools():
    print("\n--- Registering Tools ---")
    tools_config = [
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
                    "url": f"{BACKEND_PUBLIC_URL}/api/v1/tavus_tools/query_database",
                    "method": "POST",
                    "timeout": 20,
                    "auth": {"type": "bearer", "token": SECRET_KEY},
                    "body_template": {"user_id": "{user_id}", "sql": "{sql}"}
                }
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "sql": {"type": "string"}
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
                    "url": f"{BACKEND_PUBLIC_URL}/api/v1/tavus_tools/search_documents",
                    "method": "POST",
                    "timeout": 20,
                    "auth": {"type": "bearer", "token": SECRET_KEY},
                    "body_template": {"user_id": "{user_id}", "query": "{query}"}
                }
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "query": {"type": "string"}
                },
                "required": ["user_id", "query"]
            }
        }
    ]

    new_tool_ids = {}
    for payload in tools_config:
        res = requests.post("https://tavusapi.com/v2/tools", headers=HEADERS, json=payload)
        if res.status_code in [200, 201]:
            tid = res.json().get("tool_id")
            print(f"Created tool {payload['name']} -> {tid}")
            new_tool_ids[payload['name']] = tid
        else:
            print(f"Failed to create {payload['name']}: {res.text}")
    return new_tool_ids

def update_codebase(tool_ids, persona_map):
    print("\n--- Updating Codebase Files ---")
    
    # 1. Update update_all_prompts.py
    filepath = "backend/scripts/update_all_prompts.py"
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Replace tool IDs robustly
        for name, new_tid in tool_ids.items():
            content = re.sub(r'("[a-zA-Z0-9]+")(\s*#\s*' + name + r')', f'"{new_tid}"\\2', content)
            
        # Replace persona IDs robustly
        for base_name, new_pid in persona_map.items():
            pattern = r'("name":\s*"' + base_name + r'[^"]*".*?"persona_id":\s*")[^"]+(")'
            content = re.sub(pattern, r'\g<1>' + new_pid + r'\g<2>', content, flags=re.DOTALL)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

    # 2. Update seed_companions.py
    filepath = "backend/scripts/seed_companions.py"
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for base_name, new_pid in persona_map.items():
            pattern = r'("name":\s*"' + base_name + r'".*?"tavus_persona_id":\s*")[^"]+(")'
            content = re.sub(pattern, r'\g<1>' + new_pid + r'\g<2>', content, flags=re.DOTALL)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

    # 3. Update sync_tool_urls.py
    filepath = "backend/scripts/sync_tool_urls.py"
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for name, new_tid in tool_ids.items():
            content = re.sub(r'("[a-zA-Z0-9]+")(\s*,\s*"' + name + r'")', f'"{new_tid}"\\2', content)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

def main():
    print("==================================================")
    print(" TEAMMATE ONBOARDING SCRIPT")
    print("==================================================")
    
    # 1. Register tools
    tool_ids = register_tools()
    
    # 2. Create Personas
    # create_personas now just needs to return a mapping from base_name to new_pid
    # Let's override it to return a map of base_name -> new_pid
    print("\n--- Creating Personas ---")
    from backend.scripts.update_all_prompts import AGENTS
    
    persona_map = {}
    for agent in AGENTS:
        name = agent["name"]
        base_name = name.split(" ")[0].strip()
        
        print(f"Creating persona for {base_name}...")
        create_payload = {
            "persona_name": name,
            "system_prompt": agent["prompt"].strip(),
            "pipeline_mode": "full"
        }
        res = requests.post("https://tavusapi.com/v2/personas", headers=HEADERS, json=create_payload)
        
        if res.status_code in [200, 201]:
            new_pid = res.json().get("persona_id")
            print(f"  Created -> {new_pid}")
            persona_map[base_name] = new_pid
            
            # Attach magic canvas
            requests.put(f"https://tavusapi.com/v2/pals/{new_pid}/skills/magic_canvas", headers=HEADERS, json={"config": {}})
            
            # Attach tools
            t_ids = list(tool_ids.values())
            if t_ids:
                requests.post(f"https://tavusapi.com/v2/pals/{new_pid}/tools", headers=HEADERS, json={"tool_ids": t_ids})
        else:
            print(f"  Failed: {res.text}")
    
    # 3. Update all files robustly
    update_codebase(tool_ids, persona_map)
            
    print("\n==================================================")
    print(" SUCCESS! Your environment is fully configured.")
    print(" Next steps:")
    print(" 1. Run: uv run python -m backend.scripts.seed_companions")
    print(" 2. Run: uv run python -m backend.scripts.sync_tool_urls")
    print(" 3. Restart your backend and frontend servers.")
    print("==================================================")

if __name__ == "__main__":
    main()
