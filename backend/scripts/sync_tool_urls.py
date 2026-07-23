"""
Run this script whenever you restart ngrok to keep the Tavus tool URLs in sync.
Usage: uv run python backend/scripts/sync_tool_urls.py
"""
import os, requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("TAVUS_API_KEY")
backend_url = os.getenv("BACKEND_URL", "").rstrip("/")

if not backend_url or "localhost" in backend_url or "127.0.0.1" in backend_url:
    print("ERROR: BACKEND_URL in .env must be a public URL (ngrok), not localhost.")
    print(f"Current value: {backend_url}")
    exit(1)

TOOLS = [
    ("t9dd35743a68b", "search_documents", f"{backend_url}/api/v1/tavus_tools/search_documents"),
    ("t457be0aac29c", "query_database",   f"{backend_url}/api/v1/tavus_tools/query_database"),
]

print(f"\nSyncing Tavus tool URLs to: {backend_url}\n")
for tool_id, name, url in TOOLS:
    res = requests.patch(
        f"https://tavusapi.com/v2/tools/{tool_id}",
        headers={"x-api-key": key, "Content-Type": "application/json"},
        json={
            "delivery": {
                "api": {
                    "url": url,
                    "auth": {
                        "type": "bearer",
                        "token": os.getenv("SECRET_KEY")
                    }
                }
            }
        }
    )
    status = "OK" if res.status_code in [200, 201] else f"FAIL ({res.status_code})"
    print(f"  {status}  {name}")
    if res.status_code not in [200, 201]:
        print(f"       {res.text[:200]}")

print("\nDone! Tool URLs are now pointing at your current ngrok tunnel.")
print("Remember: run this again every time you restart ngrok.\n")
