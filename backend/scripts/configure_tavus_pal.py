import os
import requests
from dotenv import load_dotenv

load_dotenv()

TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")
if not TAVUS_API_KEY:
    print("Error: Missing TAVUS_API_KEY in .env")
    exit(1)

HEADERS = {
    "x-api-key": TAVUS_API_KEY,
    "Content-Type": "application/json"
}

PAL_ID = "p7a2f792c2ba"

TOOL_IDS = [
    "t457be0aac29c", # query_database
    "t9dd35743a68b", # search_documents
    "tf52e014e6351"  # get_conversation_history
]

def main():
    # 1. Update PAL to use Tavus-hosted LLM (gpt-4o)
    patch_url = f"https://tavusapi.com/v2/pals/{PAL_ID}"
    patch_payload = [
        {
            "op": "replace",
            "path": "/pipeline_mode",
            "value": "full"
        },
        {
            "op": "replace",
            "path": "/layers/llm/model",
            "value": "gpt-4o"
        }
    ]
    
    print(f"Updating PAL {PAL_ID} to use gpt-4o...")
    patch_headers = HEADERS.copy()
    patch_headers["Content-Type"] = "application/json-patch+json"
    res = requests.patch(patch_url, headers=patch_headers, json=patch_payload)
    if res.status_code in [200, 204]:
        print("Successfully updated PAL pipeline mode.")
    else:
        print(f"Failed to update PAL: {res.text}")

    # 2. Attach tools
    print(f"Attaching tools {TOOL_IDS}...")
    attach_url = f"https://tavusapi.com/v2/pals/{PAL_ID}/tools"
    res = requests.post(attach_url, headers=HEADERS, json={"tool_ids": TOOL_IDS})
    if res.status_code in [200, 201]:
        print(f"Successfully attached tools")
    else:
        print(f"Failed to attach tools: {res.text}")

    # 3. Attach magic_canvas skill
    print("Attaching magic_canvas skill...")
    skill_url = f"https://tavusapi.com/v2/pals/{PAL_ID}/skills/magic_canvas"
    res = requests.put(skill_url, headers=HEADERS, json={"config": {}})
    if res.status_code in [200, 201]:
        print("Successfully attached magic_canvas skill")
    else:
        print(f"Failed to attach magic_canvas: {res.text}")

if __name__ == "__main__":
    main()
