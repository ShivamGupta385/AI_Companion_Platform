"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { chatService } from "@/services/chat.service";
import { Message } from "@/types/chat.types";

import ChatWindow from "@/components/chat/ChatWindow";
import ChatInput from "@/components/chat/ChatInput";
import TypingIndicator from "@/components/chat/TypingIndicator";
import LiveAvatar from "@/components/avatar/LiveAvatar";

interface ChatSendResponse {
  response: string;
  retrieved_context?: string;
  graph_context?: string;
  hybrid_context?: string;
}

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();

  const conversationId =
    params.conversationId as string;

  const [messages, setMessages] =
    useState<Message[]>([]);

  const [loading, setLoading] =
    useState(false);

  // -----------------------------------
  // Latest AGIX assistant reply
  // This will be passed to LiveAvatar
  // -----------------------------------
  const [lastAssistantMessage, setLastAssistantMessage] =
    useState("");

  // -----------------------------------
  // Graph RAG debug states
  // -----------------------------------
  const [retrievedContext, setRetrievedContext] =
    useState("");

  const [graphContext, setGraphContext] =
    useState("");

  const [hybridContext, setHybridContext] =
    useState("");

  const [showDebugPanel, setShowDebugPanel] =
    useState(true);

  const loadMessages = async () => {
    try {
      const data =
        await chatService.getMessages(
          conversationId
        );

      setMessages(data);
    } catch (error) {
      console.error(
        "Load messages error:",
        error
      );
    }
  };

  useEffect(() => {
    if (conversationId) {
      loadMessages();
    }
  }, [conversationId]);

  const handleSend = async (
    message: string
  ) => {
    try {
      setLoading(true);

      const result: ChatSendResponse =
        await chatService.sendMessage(
          conversationId,
          message
        );

      // -----------------------------------
      // Save latest AGIX response for avatar
      // -----------------------------------
      setLastAssistantMessage(
        result.response || ""
      );

      // -----------------------------------
      // Save Graph RAG / Vector RAG debug info
      // -----------------------------------
      setRetrievedContext(
        result.retrieved_context || ""
      );

      setGraphContext(
        result.graph_context || ""
      );

      setHybridContext(
        result.hybrid_context || ""
      );

      await loadMessages();
    } catch (error) {
      console.error(
        "Send message error:",
        error
      );
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
              onClick={() =>
                router.push("/companions")
              }
              className="
                px-4
                py-2
                rounded-xl
                border
                border-[#ECEAF4]
                bg-white
                hover:bg-slate-50
                transition
              "
            >
              ← Back
            </button>

            <div
              className="
                h-14
                w-14
                rounded-2xl
                bg-gradient-to-r
                from-violet-500
                to-purple-600
                flex
                items-center
                justify-center
                text-white
                text-xl
              "
            >
              🤖
            </div>

            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                AI Companion Chat
              </h1>

              <p className="text-sm text-slate-500">
                Personalized AI Assistant + LiveAvatar
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() =>
                setShowDebugPanel(
                  !showDebugPanel
                )
              }
              className="
                px-4
                py-2
                rounded-xl
                bg-violet-50
                text-violet-700
                border
                border-violet-200
                hover:bg-violet-100
                transition
                text-sm
                font-medium
              "
            >
              {showDebugPanel
                ? "Hide Graph RAG"
                : "Show Graph RAG"}
            </button>

            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />

              <span className="text-green-600 text-sm font-medium">
                Online
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat + Graph RAG Layout */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full max-w-[1600px] mx-auto px-6 py-6 flex gap-6">
          {/* Left Chat Section */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex-1 overflow-y-auto">
              <div className="max-w-6xl mx-auto px-2 py-2">
                {/* LiveAvatar */}
                <div className="mb-8">
                  <LiveAvatar
                    lastAssistantMessage={lastAssistantMessage}
                  />
                </div>

                {messages.length === 0 ? (
                  <div className="flex flex-col items-center text-center mt-10">
                    <img
                      src="/companion/robot.png"
                      alt="AI Companion"
                      className="w-[260px] mb-8"
                    />

                    <h2 className="text-6xl font-bold text-slate-900">
                      Start a{" "}
                      <span className="text-violet-600">
                        Conversation
                      </span>
                    </h2>

                    <p className="mt-4 text-slate-500">
                      Ask anything to your AI Companion
                    </p>

                    <div
                      className="
                        grid
                        md:grid-cols-3
                        gap-4
                        mt-10
                        w-full
                        max-w-4xl
                      "
                    >
                      <button
                        onClick={() =>
                          handleSend(
                            "Help me plan my studies"
                          )
                        }
                        className="
                          bg-white
                          border
                          border-[#ECEAF4]
                          rounded-3xl
                          p-5
                          text-left
                          hover:border-violet-300
                          transition
                        "
                      >
                        📚 Help me plan my studies
                      </button>

                      <button
                        onClick={() =>
                          handleSend(
                            "Guide me to stay productive"
                          )
                        }
                        className="
                          bg-white
                          border
                          border-[#ECEAF4]
                          rounded-3xl
                          p-5
                          text-left
                          hover:border-violet-300
                          transition
                        "
                      >
                        🚀 Guide me to stay productive
                      </button>

                      <button
                        onClick={() =>
                          handleSend(
                            "Help me achieve my goals"
                          )
                        }
                        className="
                          bg-white
                          border
                          border-[#ECEAF4]
                          rounded-3xl
                          p-5
                          text-left
                          hover:border-violet-300
                          transition
                        "
                      >
                        🎯 Help me achieve my goals
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

                    {loading && (
                      <TypingIndicator />
                    )}
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
                  onDocumentUploaded={(
                    fileName
                  ) => {
                    console.log(
                      "Uploaded document:",
                      fileName
                    );
                  }}
                />
              </div>
            </div>
          </div>

          {/* Right Debug Panel */}
          {showDebugPanel && (
            <div
              className="
                w-[420px]
                shrink-0
                bg-white
                border
                border-[#ECEAF4]
                rounded-3xl
                shadow-sm
                overflow-hidden
                flex
                flex-col
              "
            >
              <div className="px-6 py-5 border-b border-[#ECEAF4]">
                <h2 className="text-xl font-bold text-slate-900">
                  Graph RAG Debug Panel
                </h2>

                <p className="text-sm text-slate-500 mt-1">
                  Inspect vector RAG, graph RAG and hybrid retrieval context
                </p>
              </div>

              <div className="flex-1 overflow-y-auto p-5 space-y-5">
                {/* Vector RAG */}
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <h3 className="text-sm font-semibold text-slate-900 mb-2">
                    Vector / Document RAG Context
                  </h3>

                  <div className="text-sm text-slate-700 whitespace-pre-wrap break-words max-h-[220px] overflow-y-auto">
                    {retrievedContext
                      ? retrievedContext
                      : "No vector/document RAG context available yet."}
                  </div>
                </div>

                {/* Graph RAG */}
                <div className="rounded-2xl border border-violet-200 bg-violet-50 p-4">
                  <h3 className="text-sm font-semibold text-violet-900 mb-2">
                    Graph RAG Context
                  </h3>

                  <div className="text-sm text-violet-800 whitespace-pre-wrap break-words max-h-[220px] overflow-y-auto">
                    {graphContext
                      ? graphContext
                      : "No graph RAG context available yet."}
                  </div>
                </div>

                {/* Hybrid Context */}
                <div className="rounded-2xl border border-cyan-200 bg-cyan-50 p-4">
                  <h3 className="text-sm font-semibold text-cyan-900 mb-2">
                    Hybrid Context
                  </h3>

                  <div className="text-sm text-cyan-800 whitespace-pre-wrap break-words max-h-[260px] overflow-y-auto">
                    {hybridContext
                      ? hybridContext
                      : "No hybrid retrieval context available yet."}
                  </div>
                </div>

                {/* Latest Assistant Response */}
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
                  <h3 className="text-sm font-semibold text-emerald-900 mb-2">
                    Latest AGIX Assistant Response
                  </h3>

                  <div className="text-sm text-emerald-800 whitespace-pre-wrap break-words max-h-[220px] overflow-y-auto">
                    {lastAssistantMessage
                      ? lastAssistantMessage
                      : "No assistant response yet."}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}