from backend.app.db.session import SessionLocal
from backend.app.models.companion import Companion

# Replace these with your FULL IDs from Tavus
FACE_ID = "r291e545fd67"
PAL_ID = "p4ee119868ef"

db = SessionLocal()

try:
    aria = (
        db.query(Companion)
        .filter(Companion.name == "Aria")
        .first()
    )

    if not aria:
        print("Aria not found!")
        exit()

    aria.avatar_provider = "tavus"
    aria.tavus_replica_id = FACE_ID
    aria.tavus_persona_id = PAL_ID

    db.commit()

    print("✅ Aria updated successfully!")
    print("Provider :", aria.avatar_provider)
    print("Replica  :", aria.tavus_replica_id)
    print("PAL      :", aria.tavus_persona_id)

finally:
    db.close()