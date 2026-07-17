"use client";

import { useState } from "react";
import { ragService } from "@/services/rag.service";

interface DocumentUploaderProps {
  companionId: string;
  companionName?: string;
  onUploadSuccess?: () => void;
}

export default function DocumentUploader({
  companionId,
  companionName,
  onUploadSuccess,
}: DocumentUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file");
      return;
    }

    if (!companionId) {
      alert("Companion ID is missing");
      return;
    }

    try {
      setLoading(true);

      console.log("Uploading:", file.name);
      console.log("Companion ID:", companionId);
      console.log("Companion Name:", companionName);

      const result = await ragService.uploadDocument(
        file,
        companionId
      );

      console.log("UPLOAD RESULT:", result);

      alert(
        `${result.file_name} uploaded successfully${
          companionName ? ` for ${companionName}` : ""
        }`
      );

      setFile(null);

      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (error) {
      console.error(error);
      alert("Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <input
        type="file"
        accept=".pdf,.txt,.docx"
        onChange={(e) =>
          setFile(e.target.files?.[0] || null)
        }
      />

      <button
        onClick={handleUpload}
        disabled={loading}
        className="
          rounded-lg
          bg-black
          px-4
          py-2
          text-white
        "
      >
        {loading ? "Uploading..." : "Upload Document"}
      </button>
    </div>
  );
}