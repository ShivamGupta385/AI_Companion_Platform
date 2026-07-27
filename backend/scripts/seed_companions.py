from backend.app.db.session import SessionLocal
from backend.app.models.companion import Companion

def seed_companions():
    db = SessionLocal()

    companions = [
        {
            "name": "Noor",
            "persona": "Wellness Guide",
            "voice_id": "noor_voice",
            "avatar_provider": "tavus",
            "tavus_replica_id": "r378d159c7b0",
            "tavus_persona_id": "p862fd5c9d7b"
        },
        {
            "name": "Rene",
            "persona": "Life Coach",
            "voice_id": "rene_voice",
            "avatar_provider": "tavus",
            "tavus_replica_id": "r987f6e6f73c",
            "tavus_persona_id": "p2c97ab1f0ba"
        },
        {
            "name": "Max",
            "persona": "Fitness Agent",
            "voice_id": "max_voice",
            "avatar_provider": "tavus",
            "tavus_replica_id": "rf8f3aa4b33e",
            "tavus_persona_id": "p0163eae69da"
        },
        {
            "name": "Victor",
            "persona": "Business Agent",
            "voice_id": "victor_voice",
            "avatar_provider": "tavus",
            "tavus_replica_id": "rdd4c86e5e1a",
            "tavus_persona_id": "p0bc5011befe"
        },
        {
            "name": "Aria",
            "persona": "Study Coach",
            "voice_id": "aria_voice",
            "avatar_provider": "tavus",
            "tavus_replica_id": "rfc63eab317e",
            "tavus_persona_id": "pcdd20ce5693"
        }
    ]

    for companion_data in companions:
        existing = (
            db.query(Companion)
            .filter(
                Companion.name == companion_data["name"]
            )
            .first()
        )

        if not existing:
            db.add(Companion(**companion_data))
        else:
            # Update existing if needed
            existing.avatar_provider = companion_data["avatar_provider"]
            existing.tavus_replica_id = companion_data["tavus_replica_id"]
            existing.tavus_persona_id = companion_data["tavus_persona_id"]

    db.commit()
    db.close()

    print("Companions seeded successfully with complete Tavus configurations!")

if __name__ == "__main__":
    seed_companions()