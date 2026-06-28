"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import dynamic from "next/dynamic";

// ✅ THE EXPERT FIX: Dynamically import LiveAvatar with SSR disabled
const LiveAvatar = dynamic(() => import("@/components/avatar/LiveAvatar"), {
  ssr: false,
});

import { chatService } from "@/services/chat.service";
import { Message } from "@/types/chat.types";
import ChatWindow from "@/components/chat/ChatWindow";
import ChatInput from "@/components/chat/ChatInput";
import TypingIndicator from "@/components/chat/TypingIndicator";
import DocumentList from "@/components/rag/DocumentList";

interface ChatSendResponse {
  response: string;
  retrieved_context?: string;
  graph_context?: string;
  hybrid_context?: string;
}

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();

  const conversationId = params.conversationId as string;
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastAssistantMessage, setLastAssistantMessage] = useState("");
  const [showDocuments, setShowDocuments] = useState(true);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [selectedDocumentName, setSelectedDocumentName] = useState<string | null>(null);

  const loadMessages = async () => {
    try {
      const data = await chatService.getMessages(conversationId);
      setMessages(data);
    } catch (error) {
      console.error("Load messages error:", error);
    }
  };

  useEffect(() => {
    if (conversationId) {
      loadMessages();
    }
  }, [conversationId]);

  const handleSend = async (message: string) => {
    try {
      setLoading(true);
      const result: ChatSendResponse = await chatService.sendMessage(
        conversationId,
        message
      );

      setLastAssistantMessage(result.response || "");
      await loadMessages();
    } catch (error) {
      console.error("Send message error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen bg-[#F8F7FC] flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-[#ECEAF4]">
        <div className="px-8 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/companions")}
              className="px-4 py-2 rounded-xl border border-[#ECEAF4] bg-white hover:bg-slate-50 transition"
            >
              ← Back
            </button>
            <div className="h-14 w-14 rounded-2xl bg-linear-to-r from-violet-500 to-purple-600 flex items-center justify-center text-white text-xl">
              🤖
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">AI Companion Chat</h1>
              <p className="text-sm text-slate-500">Personalized AI Assistant + LiveAvatar</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowDocuments(!showDocuments)}
              className="px-4 py-2 rounded-xl bg-violet-50 text-violet-700 border border-violet-200 hover:bg-violet-100 transition text-sm font-medium"
            >
              {showDocuments ? "Hide Documents" : "Show Documents"}
            </button>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-green-600 text-sm font-medium">Online</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Layout */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full max-w-[1600px] mx-auto px-6 py-6 flex gap-6">
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex-1 overflow-y-auto">
              <div className="max-w-6xl mx-auto px-2 py-2">
                
                {/* LiveAvatar - Dynamically Loaded */}
                <div className="mb-8">
                  <LiveAvatar lastAssistantMessage={lastAssistantMessage} />
                </div>

                {messages.length === 0 ? (
                  <div className="flex flex-col items-center text-center mt-10">
                    <img src="/companion/robot.png" alt="AI Companion" className="w-65 mb-8" />
                    <h2 className="text-6xl font-bold text-slate-900">
                      Start a <span className="text-violet-600">Conversation</span>
                    </h2>
                    <p className="mt-4 text-slate-500">Ask anything to your AI Companion</p>
                  </div>
                ) : (
                  <>
                    <ChatWindow
                      messages={messages}
                      onSpeakStart={() => {}}
                      onSpeakEnd={() => {}}
                    />
                    {loading && <TypingIndicator />}
                  </>
                )}
              </div>
            </div>

            {/* Input Area */}
            <div className="bg-white border-t border-[#ECEAF4] rounded-t-3xl mt-4">
              <div className="max-w-6xl mx-auto p-5">
                <ChatInput
                  loading={loading}
                  onSend={handleSend}
                  onDocumentUploaded={(fileName) => console.log("Uploaded:", fileName)}
                />
              </div>
            </div>
          </div>

          {/* Right Documents Panel */}
          {showDocuments && (
            <div className="w-105 shrink-0 bg-white border border-[#ECEAF4] rounded-3xl shadow-sm overflow-hidden flex flex-col">
              <div className="px-6 py-5 border-b border-[#ECEAF4]">
                <h2 className="text-xl font-bold text-slate-900">Shared Documents</h2>
              </div>
              <div className="flex-1 overflow-y-auto p-5">
                <DocumentList
                  selectedDocumentId={selectedDocumentId}
                  onSelect={(id, name) => {
                    setSelectedDocumentId(id);
                    setSelectedDocumentName(name);
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}