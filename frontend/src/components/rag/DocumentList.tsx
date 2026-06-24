"use client";

import { useEffect, useState } from "react";
import {
  documentService,
  Document,
} from "@/services/document.service";

interface Props {
  selectedDocumentId: string | null;
  onSelect: (id: string, name: string) => void;
}

export default function DocumentList({
  selectedDocumentId,
  onSelect,
}: Props) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const data = await documentService.getDocuments();

        console.log("DOCUMENTS RECEIVED:", data);
        setDocuments(data);
      } catch (error: any) {
        console.error("DOCUMENT FETCH ERROR:", error);
        console.log("STATUS:", error.response?.status);
        console.log("DATA:", error.response?.data);
      } finally {
        setLoading(false);
      }
    };

    loadDocuments();
  }, []);

  if (loading) {
    return (
      <p className="text-sm text-slate-500">
        Loading documents...
      </p>
    );
  }

  return (
    <div>
      <h3 className="mb-4 text-lg font-semibold text-slate-900">
        Uploaded Documents
      </h3>

      <div className="space-y-3">
        {documents.length === 0 ? (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
            No documents uploaded
          </div>
        ) : (
          documents.map((document) => (
            <div
              key={document.id}
              onClick={() =>
                onSelect(document.id, document.file_name)
              }
              className={`flex cursor-pointer items-center justify-between rounded-2xl border p-3 text-sm transition ${
                selectedDocumentId === document.id
                  ? "border-violet-500 bg-violet-50"
                  : "border-slate-200 bg-slate-50 hover:bg-slate-100"
              }`}
            >
              <div className="flex min-w-0 flex-1 items-center gap-3">
                <span className="text-base">📄</span>

                <div className="min-w-0">
                  <p className="truncate font-medium text-slate-800">
                    {document.file_name}
                  </p>
                </div>
              </div>

              <button
                onClick={async (e) => {
                  e.stopPropagation();

                  const confirmed = window.confirm(
                    `Delete ${document.file_name}?`
                  );

                  if (!confirmed) return;

                  try {
                    await documentService.deleteDocument(
                      document.id
                    );

                    setDocuments((prev) =>
                      prev.filter(
                        (doc) => doc.id !== document.id
                      )
                    );
                  } catch (error) {
                    console.error(error);
                    alert("Failed to delete document");
                  }
                }}
                className="ml-3 text-lg text-red-500 transition hover:text-red-700"
                title="Delete document"
              >
                🗑️
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}