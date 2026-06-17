from backend.app.db.session import SessionLocal
from backend.app.models.companion import Companion


def seed_companions():
    db = SessionLocal()

    companions = [
        {
            "name": "Aria",
            "persona": "Study Coach",
            "voice_id": "aria_voice"
        },
        {
            "name": "Noor",
            "persona": "Wellness Guide",
            "voice_id": "noor_voice"
        },
        {
            "name": "Rene",
            "persona": "Life Coach",
            "voice_id": "rene_voice"
        },
        {
            "name": "Max",
            "persona": "Fitness Agent",
            "voice_id": "max_voice"
        },
        {
            "name": "Victor",
            "persona": "Business Agent",
            "voice_id": "victor_voice"
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
            db.add(
                Companion(**companion_data)
            )

    db.commit()
    db.close()

    print("Companions seeded successfully!")


if __name__ == "__main__":
    seed_companions()