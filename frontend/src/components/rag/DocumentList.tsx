"use client";

import {
  useEffect,
  useState
} from "react";

import {
  documentService,
  Document
} from "@/services/document.service";

interface Props {

  selectedDocumentId:
    string | null;

  onSelect: (
    id: string,
    name: string
  ) => void;

}

export default function DocumentList({
  selectedDocumentId,
  onSelect
}: Props) {

  const [
    documents,
    setDocuments
  ] = useState<Document[]>([]);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {

    const loadDocuments =
      async () => {

        try {

          const data =
            await documentService.getDocuments();

          console.log(
            "DOCUMENTS RECEIVED:",
            data
          );

          setDocuments(data);

        } catch (error: any) {

          console.error(
            "DOCUMENT FETCH ERROR:",
            error
          );

          console.log(
            "STATUS:",
            error.response?.status
          );

          console.log(
            "DATA:",
            error.response?.data
          );

        } finally {

          setLoading(false);
        }
      };

    loadDocuments();

  }, []);

  if (loading) {

    return (
      <p className="text-sm text-gray-500">
        Loading documents...
      </p>
    );
  }

  return (

    <div>

      <h3
        className="
          font-semibold
          text-lg
          mb-3
          mt-6
        "
      >
        Uploaded Documents
      </h3>

      <div className="space-y-2">

        {documents.length === 0 ? (

          <p className="text-sm text-gray-500">
            No documents uploaded
          </p>

        ) : (

          documents.map(
  (document) => (

    <div
      key={document.id}
      onClick={() =>
        onSelect(
          document.id,
          document.file_name
        )
      }
      className={`
        flex
        items-center
        justify-between
        p-3
        border
        rounded-xl
        cursor-pointer
        transition
        text-sm

        ${
          selectedDocumentId ===
          document.id
            ? "bg-blue-100 border-blue-500"
            : "bg-gray-50 hover:bg-gray-100"
        }
      `}
    >

      <div
        className="
          flex
          items-center
          gap-2
          flex-1
          overflow-hidden
        "
      >

        <span>📄</span>

        <span
          className="
            truncate
          "
        >
          {document.file_name}
        </span>

      </div>

      <button
        onClick={async (e) => {

          e.stopPropagation();

          const confirmed =
            window.confirm(
              `Delete ${document.file_name}?`
            );

          if (!confirmed) {
            return;
          }

          try {

            await documentService.deleteDocument(
              document.id
            );

            setDocuments(
              documents.filter(
                (doc) =>
                  doc.id !== document.id
              )
            );

          } catch (error) {

            console.error(error);

            alert(
              "Failed to delete document"
            );

          }

        }}
        className="
          ml-2
          text-red-500
          hover:text-red-700
          text-lg
        "
      >
        🗑️
      </button>

    </div>

  )
)

        )}

      </div>

    </div>

  );
}