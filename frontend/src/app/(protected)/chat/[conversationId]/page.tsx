"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Bot,
  FileText,
  Sparkles,
  Brain,
  ArrowLeft,
} from "lucide-react";

import { chatService } from "@/services/chat.service";
import { Message } from "@/types/chat.types";

import ChatWindow from "@/components/chat/ChatWindow";
import ChatInput from "@/components/chat/ChatInput";
import TypingIndicator from "@/components/chat/TypingIndicator";
import LiveAvatar from "@/components/avatar/LiveAvatar";
import TavusAvatar from "@/components/avatar/TavusAvatar";

interface ChatSendResponse {
  response: string;
  retrieved_context?: string;
  graph_context?: string;
  hybrid_context?: string;
}

interface ConversationDetails {
  id: string;
  companion_id: string;
  companion_name?: string;
}

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();

  const conversationId = params.conversationId as string;

  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  // Companion info for document upload
  const [companionId, setCompanionId] = useState("");
  const [companionName, setCompanionName] = useState("");

  // Latest assistant reply for avatar
  const [lastAssistantMessage, setLastAssistantMessage] =
    useState("");

  // Document panel states
  const [selectedDocumentId, setSelectedDocumentId] =
    useState<string | null>(null);

  const [selectedDocumentName, setSelectedDocumentName] =
    useState<string | null>(null);

  const loadMessages = async () => {
    try {
      const data = await chatService.getMessages(
        conversationId
      );
      setMessages(data);
    } catch (error) {
      console.error("Load messages error:", error);
    }
  };

  const loadConversationDetails = async () => {
    try {
      const conversation: ConversationDetails =
        await chatService.getConversationById(
          conversationId
        );

      console.log(
        "[CHAT PAGE] Conversation details:",
        conversation
      );

      setCompanionId(conversation.companion_id || "");
      setCompanionName(
        conversation.companion_name || ""
      );
    } catch (error) {
      console.error(
        "Load conversation details error:",
        error
      );
    }
  };

  useEffect(() => {
    if (conversationId) {
      loadMessages();
      loadConversationDetails();
    }
  }, [conversationId]);

  const handleSend = async (message: string) => {
    try {
      setLoading(true);

      const result: ChatSendResponse =
        await chatService.sendMessage(
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

  const shortConversationId = conversationId
    ? conversationId.slice(0, 8)
    : "";

  return (
    <div className="flex h-screen flex-col bg-[#F8F7FC]">
      {/* Header */}
      <div className="border-b border-[#ECEAF4] bg-white/90 backdrop-blur">
        <div className="flex items-center justify-between px-8 py-5">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/companions")}
              className="flex items-center gap-2 rounded-2xl border border-[#ECEAF4] bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
            >
              <ArrowLeft size={16} />
              Back
            </button>

            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-300/40">
              <Bot size={26} />
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-2xl font-bold text-slate-900">
                  AI Companion Chat
                </h1>

                {companionName && (
                  <span className="rounded-full bg-violet-100 px-3 py-1 text-xs font-semibold text-violet-700">
                    {companionName}
                  </span>
                )}

                {shortConversationId && (
                  <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-500">
                    Chat #{shortConversationId}
                  </span>
                )}
              </div>

              <p className="mt-1 text-sm text-slate-500">
                Personalized AI assistant with memory,
                document understanding, and companion-aware
                chat.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2">
              <div className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-sm font-medium text-emerald-700">
                Online
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Layout */}
      <div className="flex-1 overflow-hidden">
        <div className="mx-auto flex h-full max-w-[1600px] gap-6 px-6 py-6">
          {/* Left Chat Section */}
          <div className="flex min-w-0 flex-1 flex-col">
            <div className="flex-1 overflow-y-auto">
              <div className="mx-auto max-w-6xl px-2 py-2">
                {/* Top AI capability badges */}
                <div className="mb-5 flex flex-wrap gap-3">
                  <div className="flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-4 py-2 text-sm text-violet-700">
                    <Sparkles size={16} />
                    AI Companion
                  </div>

                  <div className="flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-700">
                    <Brain size={16} />
                    Conversation Memory
                  </div>

                  <div className="flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-700">
                    <FileText size={16} />
                    Shared Documents
                  </div>
                </div>

                {/* Live Avatar */}
                <div className="mb-8">
                  <LiveAvatar
                    lastAssistantMessage={lastAssistantMessage}
                  />

                  {/*<TavusAvatar
                      companionId={companionId}
                  />*/}
                </div>

                {messages.length === 0 ? (
                  <div className="mt-10 flex flex-col items-center text-center">
                    <img
                      src="/companion/robot.png"
                      alt="AI Companion"
                      className="mb-8 w-[240px] drop-shadow-md"
                    />

                    <h2 className="max-w-4xl text-5xl font-bold leading-tight text-slate-900 md:text-6xl">
                      Start a{" "}
                      <span className="bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
                        smart conversation
                      </span>{" "}
                      with your companion
                    </h2>

                    <p className="mt-4 max-w-2xl text-base text-slate-500">
                      Ask questions, upload companion-specific
                      documents, and continue context-aware
                      conversations with memory-powered AI.
                    </p>

                    {companionName && (
                      <div className="mt-5 rounded-2xl border border-violet-200 bg-violet-50 px-5 py-3 text-sm text-violet-700">
                        You are currently chatting with{" "}
                        <span className="font-semibold">
                          {companionName}
                        </span>
                      </div>
                    )}

                    <div className="mt-10 grid w-full max-w-5xl gap-4 md:grid-cols-3">
                      <button
                        onClick={() =>
                          handleSend("Help me plan my studies")
                        }
                        className="rounded-3xl border border-[#ECEAF4] bg-white p-5 text-left shadow-sm transition hover:-translate-y-1 hover:border-violet-300 hover:shadow-md"
                      >
                        <div className="mb-3 text-2xl">📚</div>
                        <h3 className="font-semibold text-slate-900">
                          Study Planning
                        </h3>
                        <p className="mt-2 text-sm text-slate-500">
                          Build a focused learning roadmap and
                          break big goals into daily tasks.
                        </p>
                      </button>

                      <button
                        onClick={() =>
                          handleSend("Guide me to stay productive")
                        }
                        className="rounded-3xl border border-[#ECEAF4] bg-white p-5 text-left shadow-sm transition hover:-translate-y-1 hover:border-violet-300 hover:shadow-md"
                      >
                        <div className="mb-3 text-2xl">🚀</div>
                        <h3 className="font-semibold text-slate-900">
                          Productivity Coaching
                        </h3>
                        <p className="mt-2 text-sm text-slate-500">
                          Get help with focus, routines,
                          execution, and getting unstuck.
                        </p>
                      </button>

                      <button
                        onClick={() =>
                          handleSend("Help me achieve my goals")
                        }
                        className="rounded-3xl border border-[#ECEAF4] bg-white p-5 text-left shadow-sm transition hover:-translate-y-1 hover:border-violet-300 hover:shadow-md"
                      >
                        <div className="mb-3 text-2xl">🎯</div>
                        <h3 className="font-semibold text-slate-900">
                          Goal Support
                        </h3>
                        <p className="mt-2 text-sm text-slate-500">
                          Turn long-term goals into a concrete
                          action plan with your AI companion.
                        </p>
                      </button>
                    </div>
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
            <div className="mt-4 rounded-t-3xl border-t border-[#ECEAF4] bg-white">
              <div className="mx-auto max-w-6xl p-5">
                <ChatInput
                  loading={loading}
                  onSend={handleSend}
                  companionId={companionId}
                  companionName={companionName}
                  onDocumentUploaded={(fileName) => {
                    console.log("Uploaded document:", fileName);
                    setSelectedDocumentName(fileName);
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}