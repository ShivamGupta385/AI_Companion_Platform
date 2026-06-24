"use client";

import { useState } from "react";
import DocumentList from "@/components/rag/DocumentList";

export default function DocumentsPanel() {
  const [showDocuments, setShowDocuments] =
    useState(true);

  const [selectedDocumentId, setSelectedDocumentId] =
    useState<string | null>(null);

  const [selectedDocumentName, setSelectedDocumentName] =
    useState<string | null>(null);

  return (
    <div className="rounded-3xl border border-[#ECEAF4] bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-[28px] font-bold text-slate-900">
            Shared Documents
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Inspect documents uploaded by the user
          </p>
        </div>

        <button
          onClick={() =>
            setShowDocuments((prev) => !prev)
          }
          className="rounded-full border border-violet-200 bg-violet-50 px-4 py-2 text-sm font-medium text-violet-700 transition hover:bg-violet-100"
        >
          {showDocuments
            ? "Hide Documents"
            : "Show Documents"}
        </button>
      </div>

      {showDocuments ? (
        <>
          <DocumentList
            selectedDocumentId={selectedDocumentId}
            onSelect={(id, name) => {
              setSelectedDocumentId(id);
              setSelectedDocumentName(name);
            }}
          />

          {selectedDocumentName && (
            <div className="mt-4 rounded-2xl border border-violet-200 bg-violet-50 p-3 text-sm text-violet-700">
              Selected:{" "}
              <span className="font-medium">
                {selectedDocumentName}
              </span>
            </div>
          )}
        </>
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
          Documents panel hidden.
        </div>
      )}
    </div>
  );
}