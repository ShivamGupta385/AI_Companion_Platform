"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft, FolderOpen } from "lucide-react";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export default function DocumentsPage() {
  const router = useRouter();
  
  // React state
  const [documents, setDocuments] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);

  // Fetch documents using the api instance
  const fetchDocuments = async () => {
    try {
      // Notice the trailing slash added to match your backend route
      const response = await api.get("/documents/");
      setDocuments(response.data);
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    }
  };

  // Load documents automatically
  useEffect(() => {
    fetchDocuments();
  }, []);

  // Upload handler using the api instance
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];

    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);

    try {
      await api.post("/documents/upload", formData);
      fetchDocuments();
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  // Delete function using the api instance
  const deleteDocument = async (id: string) => {
    try {
      await api.delete(`/documents/${id}`);
      fetchDocuments();
    } catch (err) {
      console.error("Failed to delete document:", err);
      alert("Delete failed");
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F7FF]">
      <main className="max-w-7xl mx-auto px-8 py-8">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-10">
          <div>
            <h1 className="text-4xl font-bold text-slate-900">
              Shared Documents
            </h1>

            <p className="mt-2 text-slate-500">
              Upload, manage and search your shared documents.
            </p>
          </div>

          <button
            onClick={() => router.back()}
            className="
              flex
              items-center
              gap-2
              rounded-xl
              bg-white
              px-5
              py-3
              shadow-sm
              hover:bg-slate-100
              transition
            "
          >
            <ArrowLeft size={18} />
            Back
          </button>
        </div>

        {/* Functional Document Card */}
        <div
          className="
            bg-white
            rounded-3xl
            shadow-sm
            p-16
            flex
            flex-col
            items-center
            justify-center
            text-center
          "
        >
          <FolderOpen size={72} className="text-emerald-500" />

          <h2 className="mt-6 text-3xl font-bold text-slate-900">
            Shared Documents
          </h2>

          <p className="mt-4 max-w-2xl text-slate-500 text-lg">
            Upload documents, browse uploaded files, and manage your knowledge base.
          </p>

          {/* Upload Button */}
          <label
            className={`
              mt-8
              rounded-2xl
              bg-linear-to-r
              from-emerald-500
              to-cyan-500
              px-8
              py-4
              text-white
              font-semibold
              cursor-pointer
              hover:opacity-90
              transition
              ${uploading ? "opacity-60 cursor-wait" : ""}
            `}
          >
            {uploading ? "Uploading..." : "Upload Document"}

            <input
              type="file"
              className="hidden"
              onChange={handleUpload}
              disabled={uploading}
            />
          </label>

          {/* Show uploaded documents */}
          {documents.length > 0 && (
            <div className="mt-10 space-y-4 w-full max-w-2xl text-left">
              {documents.map((doc: any) => (
                <div
                  key={doc.id}
                  className="
                    bg-slate-50
                    rounded-xl
                    p-5
                    flex
                    justify-between
                    items-center
                  "
                >
                  <div>
                    <p className="font-semibold text-slate-900">
                      {doc.file_name}
                    </p>
                    <p className="text-sm text-slate-500">
                      {new Date(doc.uploaded_at).toLocaleString()}
                    </p>
                  </div>

                  <button
                    onClick={() => deleteDocument(doc.id)}
                    className="
                      bg-red-500
                      hover:bg-red-600
                      transition
                      text-white
                      px-4
                      py-2
                      rounded-lg
                    "
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}