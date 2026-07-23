"use client";

import { useState, useRef, useEffect } from "react";
import {
  Paperclip,
  Mic,
  Send,
  X,
  FileText,
} from "lucide-react";

import { ragService } from "@/services/rag.service";

interface ChatInputProps {
  onSend: (message: string) => void;
  loading: boolean;
  autoSendVoice?: boolean;
  onDocumentUploaded?: (documentName: string) => void;
  companionId?: string;
}

export default function ChatInput({
  onSend,
  loading,
  autoSendVoice = false,
  onDocumentUploaded,
  companionId,
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [listening, setListening] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);
  const transcriptRef = useRef<string>("");

  // Step 4 & 5: Initialize SpeechRecognition once with better settings
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.continuous = false;
      recognition.interimResults = true; // Step 5: Live updates
      recognition.maxAlternatives = 1; // Step 5: Single best result
      
      recognitionRef.current = recognition;
    }
  }, []);

  const handleSend = () => {
    if ((!message.trim() && !selectedFile) || loading) {
      return;
    }

    onSend(message);
    setMessage("");
  };

  const startListening = () => {
    console.log("🎤 Mic button clicked");

    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    console.log("SpeechRecognition:", SpeechRecognition);

    if (!SpeechRecognition) {
      alert("Speech Recognition not supported");
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      console.log("✅ Recognition started");
      setListening(true);
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;

      console.log("🎤 Transcript:", transcript);

      setMessage(transcript);

      if (autoSendVoice) {
        onSend(transcript);

        setMessage("");
      }
    };

    recognition.onerror = (event: any) => {
      console.log("❌ ERROR:", event.error);
    };

    recognition.onend = () => {
      console.log("🛑 Recognition ended");
      setListening(false);
    };

    console.log("Calling recognition.start()");
    recognition.start();
  };

  const handleFileSelect = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setSelectedFile(file);
      setUploading(true);

      const result = await ragService.uploadDocument(file, companionId || "");
      console.log("Uploaded:", result);
      onDocumentUploaded?.(result.file_name);
    } catch (error) {
      console.error(error);
      alert("Document upload failed");
      setSelectedFile(null);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      {selectedFile && (
        <div
          className="
            mb-3
            flex
            items-center
            justify-between
            rounded-2xl
            border
            border-violet-200
            bg-violet-50
            px-4
            py-3
          "
        >
          <div className="flex items-center gap-2">
            <FileText
              size={18}
              className="text-violet-600"
            />
            <span
              className="
                text-sm
                text-violet-700
              "
            >
              {selectedFile.name}
              {uploading && " (Uploading...)"}
            </span>
          </div>

          <button
            onClick={() => setSelectedFile(null)}
            className="
              text-red-500
              hover:text-red-700
            "
          >
            <X size={16} />
          </button>
        </div>
      )}

      <div
        className="
          bg-white
          rounded-[28px]
          border
          border-[#ECEAF4]
          shadow-sm
          px-4
          py-3
        "
      >
        <div className="flex items-center gap-3">
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.txt,.doc,.docx"
            onChange={handleFileSelect}
          />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="
              w-10
              h-10
              rounded-full
              flex
              items-center
              justify-center
              text-slate-500
              hover:bg-slate-100
              transition
            "
          >
            <Paperclip size={18} />
          </button>

          <input
            type="text"
            placeholder={
              listening
                ? "Listening..."
                : loading
                ? "Processing..."
                : "Type your message..."
            }
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSend();
              }
            }}
            disabled={listening}
            className="
              flex-1
              outline-none
              bg-transparent
              text-slate-700
              placeholder:text-slate-400
              disabled:opacity-70
            "
          />

          {/* Step 3: Better microphone UX states */}
          <button
            onClick={startListening}
            type="button"
            disabled={listening || loading}
            className={`
              w-10
              h-10
              rounded-full
              border
              flex
              items-center
              justify-center
              transition-all
              ${
                listening
                  ? "border-red-500 text-red-500 bg-red-50 animate-pulse" // Red/Listening state
                  : loading
                  ? "border-slate-200 text-slate-400 cursor-not-allowed" // Processing state
                  : "border-[#ECEAF4] text-violet-600 hover:bg-violet-50" // Idle state
              }
            `}
          >
            <Mic size={18} />
          </button>

          <button
            onClick={handleSend}
            disabled={loading || uploading || (!message.trim() && !selectedFile)}
            className="
              flex
              items-center
              gap-2
              px-6
              py-3
              rounded-2xl
              bg-linear-to-r
              from-violet-500
              to-purple-600
              text-white
              font-medium
              shadow-lg
              shadow-violet-300/40
              hover:scale-105
              transition-all
              disabled:opacity-50
              disabled:hover:scale-100
            "
          >
            {loading ? "..." : "Send"}
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}