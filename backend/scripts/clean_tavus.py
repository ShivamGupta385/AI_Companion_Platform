import os
import requests
from dotenv import load_dotenv

load_dotenv()

TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")

HEADERS = {
    "x-api-key": TAVUS_API_KEY,
    "Content-Type": "application/json"
}

KEEP_IDS = [
    "pb14a5e2b2f2", # Aria
    "p62279f64e97", # Noor
    "p586f4dc3f09", # Rene
    "p960a8cb833a", # Max
    "p4262f25b8e5"  # Victor
]

def clean_personas():
    url = "https://tavusapi.com/v2/personas?limit=100"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        data = res.json().get("data", [])
        for p in data:
            pid = p.get('persona_id')
            pname = p.get('persona_name')
            if pid not in KEEP_IDS:
                print(f"Deleting {pname} ({pid})...")
                del_res = requests.delete(f"https://tavusapi.com/v2/personas/{pid}", headers=HEADERS)
                if del_res.status_code in [200, 204]:
                    print(f"  -> Deleted successfully.")
                else:
                    print(f"  -> Failed to delete: {del_res.status_code} {del_res.text}")
            else:
                print(f"KEEPING {pname} ({pid})")
    else:
        print("Failed to fetch personas:", res.text)

if __name__ == "__main__":
    clean_personas()
