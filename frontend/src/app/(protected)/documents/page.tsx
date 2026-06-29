"use client";

import DocumentsPanel from "@/components/rag/DocumentsPanel";

export default function DocumentsPage() {
  return (
    <div className="min-h-screen bg-[#F8F7FF] p-6">
      <div className="mx-auto max-w-6xl">
        <DocumentsPanel />
      </div>
    </div>
  );
}