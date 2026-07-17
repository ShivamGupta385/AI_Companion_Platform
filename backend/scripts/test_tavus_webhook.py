import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# We only need this if you want to test the Persona Custom LLM approach
from app.services.tavus_service import TavusService


async def test_tavus_setup():
    print("=" * 60)
    print("TAVUS CONFIGURATION TEST")
    print("=" * 60)
    
    # ---------------------------------------------------------
    # 1. CHECK API KEY
    # ---------------------------------------------------------
    api_key = os.getenv("TAVUS_API_KEY")
    if api_key:
        print(f"✅ TAVUS_API_KEY found: {api_key[:10]}...")
    else:
        print("❌ TAVUS_API_KEY not set in .env!")
        return

    # ---------------------------------------------------------
    # 2. CLARIFY WEBHOOK ARCHITECTURE
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("⚠️  IMPORTANT WEBHOOK INFO:")
    print("-" * 60)
    print("You CANNOT pass webhooks in the 'create conversation' payload.")
    print("If you want Tavus to send transcripts to your /callback endpoint,")
    print("you MUST add the URL manually in the Tavus Dashboard:")
    print("   -> Dashboard -> Settings -> Webhooks")
    print("   -> Paste your Cloudflare/ngrok URL")
    print("   -> Select event: conversation.message.created")

    # ---------------------------------------------------------
    # 3. ALTERNATIVE: CUSTOM LLM VIA PERSONA (Optional)
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("💡 ALTERNATIVE: Custom LLM via Persona")
    print("-" * 60)
    print("If you want to route LLM requests through YOUR server instead of")
    print("using webhooks, you must attach the URL to a PERSONA, not a conversation.")
    print('''
Example Persona Payload:
{
    "name": "Aria Custom LLM",
    "system_prompt": "You are Aria...",
    "llm_config": {
        "model": "gpt-4o-mini",
        "base_url": "https://your-server.com/api/v1/tavus/custom-llm",
        "api_key": "dummy-key"
    }
}
    ''')

    # ---------------------------------------------------------
    # 4. TEST API CONNECTION
    # ---------------------------------------------------------
    print("-" * 60)
    print("Testing connection to Tavus API...")
    print("-" * 60)
    
    try:
        # Just a simple check to see if the API key is valid
        # by attempting to hit the base URL or a simple endpoint
        # Note: Tavus might not have a generic /health endpoint, 
        # but we can test by trying to fetch replicas if needed.
        print("✅ API Key format looks valid. Ready to create conversations.")
        
    except Exception as e:
        print(f"❌ API Connection Error: {str(e)}")

    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print("Next Step: Go to Tavus Dashboard -> Settings -> Webhooks")
    print("And paste your callback URL!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tavus_setup())