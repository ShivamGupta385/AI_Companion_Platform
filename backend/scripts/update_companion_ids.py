from backend.app.db.session import SessionLocal
from backend.app.models.companion import Companion

def main():
    db = SessionLocal()
    
    updates = {
        "Noor": {"replica": "r378d159c7b0", "persona": "p62279f64e97"},
        "Rene": {"replica": "r987f6e6f73c", "persona": "p586f4dc3f09"},
        "Max": {"replica": "rf8f3aa4b33e", "persona": "p960a8cb833a"},
        "Victor": {"replica": "rdd4c86e5e1a", "persona": "p1961dfe328e"}
    }
    
    for name, ids in updates.items():
        companion = db.query(Companion).filter(Companion.name == name).first()
        if companion:
            companion.tavus_replica_id = ids["replica"]
            companion.tavus_persona_id = ids["persona"]
            companion.avatar_provider = "tavus"
            print(f"Updated {name}")
        else:
            print(f"Companion {name} not found in DB!")
            
    db.commit()
    db.close()
    print("Database update complete!")

if __name__ == "__main__":
    main()
