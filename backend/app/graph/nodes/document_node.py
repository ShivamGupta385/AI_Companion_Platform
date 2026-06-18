from backend.app.db.session import SessionLocal
from backend.app.models.document import Document


def document_node(state):

    db = SessionLocal()

    try:

        documents = (
            db.query(Document)
            .filter(
                Document.user_id == state["user_id"]
            )
            .order_by(
                Document.uploaded_at.desc()
            )
            .all()
        )

        document_names = [
            doc.file_name
            for doc in documents
        ]

        print("=" * 50)
        print(
            "USER ID:",
            state["user_id"]
        )
        print(
            "DOCUMENTS FOUND:",
            len(documents)
        )
        print(
            "DOCUMENT NAMES:",
            document_names
        )
        print("=" * 50)

        return {
            **state,
            "document_names": document_names
        }

    except Exception as e:

        print(
            f"Document Node Error: {e}"
        )

        return {
            **state,
            "document_names": []
        }

    finally:

        db.close()