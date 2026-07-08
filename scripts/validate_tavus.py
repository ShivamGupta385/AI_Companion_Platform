import os
import sys
import requests
from dotenv import load_dotenv

def run_diagnostics():
    print("=" * 60)
    print("TAVUS DIAGNOSTICS & VALIDATION")
    print("=" * 60)

    # 1. Check Environment Variables
    load_dotenv("c:/Users/shiva/ai-companion-platform/.env")
    api_key = os.getenv("TAVUS_API_KEY")
    
    if not api_key:
        print("❌ ERROR: TAVUS_API_KEY is missing from your .env file.")
        sys.exit(1)
    print("✅ TAVUS_API_KEY is present.")

    # 2. Check API Authentication
    headers = {"x-api-key": api_key}
    print("\nChecking API Authentication...")
    resp = requests.get("https://tavusapi.com/v2/replicas", headers=headers)
    if resp.status_code == 401 or resp.status_code == 403:
        print(f"❌ ERROR: Your TAVUS_API_KEY is invalid or unauthorized. (HTTP {resp.status_code})")
        sys.exit(1)
    elif resp.status_code != 200:
        print(f"❌ ERROR: Failed to connect to Tavus API. (HTTP {resp.status_code})")
        sys.exit(1)
    print("✅ Successfully authenticated with Tavus API.")

    # 3. Check Database for Aria
    print("\nChecking Database for Aria's Configuration...")
    try:
        sys.path.insert(0, "c:/Users/shiva/ai-companion-platform")
        from backend.app.db.session import SessionLocal
        from backend.app.models.companion import Companion
        db = SessionLocal()
        aria = db.query(Companion).filter(Companion.name == "Aria").first()
        if not aria:
            print("❌ ERROR: Aria companion not found in the database.")
            sys.exit(1)
        
        persona_id = aria.tavus_persona_id
        replica_id = aria.tavus_replica_id
        
        print(f"✅ Found Aria. Persona ID: {persona_id}, Face ID: {replica_id}")
    except Exception as e:
        print(f"❌ ERROR: Database check failed: {e}")
        sys.exit(1)
    finally:
        db.close()

    if not persona_id:
        print("❌ ERROR: Aria does not have a Tavus Persona ID assigned in the database.")
        sys.exit(1)

    # 4. Validate Persona ID
    print(f"\nValidating Persona ID ({persona_id}) on Tavus...")
    resp = requests.get(f"https://tavusapi.com/v2/personas/{persona_id}", headers=headers)
    
    if resp.status_code == 404:
        print(f"❌ ERROR: The Persona ID {persona_id} DOES NOT EXIST under this API key. Make sure they are in the same workspace.")
        sys.exit(1)
    elif resp.status_code != 200:
        print(f"❌ ERROR: Failed to fetch persona details. (HTTP {resp.status_code})")
        sys.exit(1)
    
    persona_data = resp.json()
    pipeline_mode = persona_data.get("pipeline_mode")
    
    if pipeline_mode != "full":
        print(f"❌ ERROR: The Persona ID {persona_id} has pipeline_mode='{pipeline_mode}'.")
        print("   It MUST be 'full' in order to hook up to your custom backend LLM.")
        print("   If you created this on the dashboard, it likely defaulted to 'conversational'.")
        print("   Please recreate the persona via API with pipeline_mode: 'full'.")
        sys.exit(1)
    print("✅ Persona exists and has the correct 'full' pipeline_mode for custom backend routing.")

    print("\n" + "=" * 60)
    print("🎉 ALL CHECKS PASSED! Your Tavus setup is perfectly configured.")
    print("=" * 60)

if __name__ == "__main__":
    run_diagnostics()
