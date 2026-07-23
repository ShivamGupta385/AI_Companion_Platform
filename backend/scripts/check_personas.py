import os, requests
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("TAVUS_API_KEY")
print(f"Using API key: {key[:8]}...")

# Check companions table for persona IDs
import sys
sys.path.append(".")
from backend.app.db.session import SessionLocal
from backend.app.models.companion import Companion

db = SessionLocal()
companions = db.query(Companion).all()
print("\nCompanions in DB:")
for c in companions:
    print(f"  {c.name}: replica={c.tavus_replica_id}, persona={c.tavus_persona_id}")
db.close()

# Fetch those persona IDs from Tavus
print("\nFetching persona details from Tavus:")
for c in companions:
    if c.tavus_persona_id:
        res = requests.get(
            f"https://tavusapi.com/v2/personas/{c.tavus_persona_id}",
            headers={"x-api-key": key}
        )
        name = res.json().get("persona_name", "N/A") if res.status_code == 200 else f"ERROR {res.status_code}"
        print(f"  {c.name}: persona_id={c.tavus_persona_id} -> Tavus name: {name}")
