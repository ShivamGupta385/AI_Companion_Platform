"use client";

import { useState } from "react";

import {
  ragService
} from "@/services/rag.service";

export default function DocumentUploader() {

  const [file, setFile] =
    useState<File | null>(
      null
    );

  const [loading, setLoading] =
    useState(false);

  const handleUpload = async () => {

  if (!file) {

    alert("Please select a file");

    return;
  }

  try {

    setLoading(true);

    console.log("Uploading:", file.name);

    const result =
      await ragService.uploadDocument(
        file
      );

    console.log(result);

    alert(
      `${result.file_name} uploaded successfully`
    );

    setFile(null);

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
          setFile(
            e.target.files?.[0] ||
            null
          )
        }
      />

      <button
        onClick={handleUpload}
        disabled={loading}
        className="
          bg-black
          text-white
          px-4
          py-2
          rounded-lg
        "
      >
        {loading
          ? "Uploading..."
          : "Upload Document"}
      </button>

    </div>
  );
}