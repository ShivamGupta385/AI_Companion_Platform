from backend.app.db.session import SessionLocal
from backend.app.models.document import Document


def document_node(state):
    db = SessionLocal()

    try:
        user_id = state.get("user_id")

        if not user_id:
            print("[DOCUMENT NODE] No user_id found in state")
            return {
                **state,
                "document_names": []
            }

        documents = (
            db.query(Document)
            .filter(Document.user_id == user_id)
            .order_by(Document.uploaded_at.desc())
            .all()
        )

        document_names = [doc.file_name for doc in documents]

        print("=" * 50)
        print("[DOCUMENT NODE]")
        print("USER ID:", user_id)
        print("DOCUMENTS FOUND:", len(documents))
        print("DOCUMENT NAMES:", document_names)
        print("=" * 50)

        return {
            **state,
            "document_names": document_names
        }

    except Exception as e:
        print(f"[DOCUMENT NODE ERROR] {e}")

        return {
            **state,
            "document_names": []
        }

    finally:
        db.close()