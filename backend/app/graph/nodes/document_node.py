from uuid import UUID

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
                "document_names": [],
                "latest_document_name": None,
                "latest_document_id": None
            }

        user_uuid = UUID(str(user_id))

        documents = (
            db.query(Document)
            .filter(Document.user_id == user_uuid)
            .order_by(Document.uploaded_at.desc())
            .all()
        )

        seen = set()
        document_names = []

        for doc in documents:
            if doc.file_name and doc.file_name not in seen:
                seen.add(doc.file_name)
                document_names.append(doc.file_name)

        latest_document = documents[0] if documents else None

        latest_document_name = (
            latest_document.file_name if latest_document else None
        )
        latest_document_id = (
            str(latest_document.id) if latest_document else None
        )

        print("=" * 60)
        print("[DOCUMENT NODE]")
        print("USER ID:", user_id)
        print("DOCUMENTS FOUND:", len(documents))
        print("UNIQUE DOCUMENT NAMES:", document_names)
        print("LATEST DOCUMENT NAME:", latest_document_name)
        print("LATEST DOCUMENT ID:", latest_document_id)
        print("=" * 60)

        return {
            **state,
            "document_names": document_names,
            "latest_document_name": latest_document_name,
            "latest_document_id": latest_document_id
        }

    except Exception as e:
        print(f"[DOCUMENT NODE ERROR] {e}")
        return {
            **state,
            "document_names": [],
            "latest_document_name": None,
            "latest_document_id": None
        }

    finally:
        db.close()