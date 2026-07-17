"use client";

import { useEffect, useState } from "react";
import { FileText, Trash2, Sparkles } from "lucide-react";
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
        setDocuments(data);
      } catch (error: any) {
        console.error("DOCUMENT FETCH ERROR:", error);
      } finally {
        setLoading(false);
      }
    };

    loadDocuments();
  }, []);

  if (loading) {
    return (
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-violet-100">
            <FileText className="h-5 w-5 text-violet-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">
              Uploaded Documents
            </h3>
            <p className="text-sm text-slate-500">
              Loading shared files...
            </p>
          </div>
        </div>

        <div className="space-y-3">
          {[1, 2, 3].map((item) => (
            <div
              key={item}
              className="animate-pulse rounded-2xl border border-slate-200 bg-slate-50 p-4"
            >
              <div className="h-4 w-2/3 rounded bg-slate-200" />
              <div className="mt-3 h-3 w-1/3 rounded bg-slate-200" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      {/* Header */}
      <div className="mb-5 flex items-start justify-between gap-4 rounded-3xl bg-gradient-to-r from-violet-50 to-purple-50 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white shadow-sm">
            <FileText className="h-5 w-5 text-violet-600" />
          </div>

          <div>
            <h3 className="text-lg font-semibold text-slate-900">
              Uploaded Documents
            </h3>
            <p className="text-sm text-slate-500">
              Manage files shared with companions
            </p>
          </div>
        </div>

        <div className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1.5 text-xs font-medium text-violet-700 shadow-sm">
          <Sparkles className="h-3.5 w-3.5" />
          {documents.length} file{documents.length !== 1 ? "s" : ""}
        </div>
      </div>

      {/* Content */}
      <div className="space-y-3">
        {documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-white shadow-sm">
              <FileText className="h-8 w-8 text-violet-500" />
            </div>

            <h4 className="text-base font-semibold text-slate-900">
              No documents uploaded yet
            </h4>
            <p className="mt-2 max-w-sm text-sm text-slate-500">
              Upload PDFs, notes, or knowledge files to connect them with your AI companions and power RAG-based conversations.
            </p>
          </div>
        ) : (
          documents.map((document) => {
            const isSelected =
              selectedDocumentId === document.id;

            return (
              <div
                key={document.id}
                onClick={() =>
                  onSelect(document.id, document.file_name)
                }
                className={`group flex cursor-pointer items-center justify-between rounded-3xl border p-4 transition-all duration-200 ${
                  isSelected
                    ? "border-violet-500 bg-violet-50 shadow-md shadow-violet-100"
                    : "border-slate-200 bg-slate-50 hover:-translate-y-0.5 hover:border-violet-200 hover:bg-white hover:shadow-md"
                }`}
              >
                <div className="flex min-w-0 flex-1 items-start gap-4">
                  {/* File Icon */}
                  <div
                    className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${
                      isSelected
                        ? "bg-white shadow-sm"
                        : "bg-white"
                    }`}
                  >
                    <FileText
                      className={`h-6 w-6 ${
                        isSelected
                          ? "text-violet-600"
                          : "text-slate-600"
                      }`}
                    />
                  </div>

                  {/* File Info */}
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-slate-900">
                      {document.file_name}
                    </p>

                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span className="text-xs text-slate-500">
                        Shared with
                      </span>

                      <span
                        className={`rounded-full px-3 py-1 text-xs font-medium ${
                          document.companion_name
                            ? "bg-violet-100 text-violet-700"
                            : "bg-slate-200 text-slate-600"
                        }`}
                      >
                        {document.companion_name || "Not assigned"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Delete Button */}
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
                  className="ml-4 flex h-10 w-10 items-center justify-center rounded-full text-slate-400 transition hover:bg-red-50 hover:text-red-600"
                  title="Delete document"
                >
                  <Trash2 className="h-4.5 w-4.5" />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}