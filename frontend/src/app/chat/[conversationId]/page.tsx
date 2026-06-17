"use client";

import {
  useEffect,
  useState
} from "react";

import {
  useParams
} from "next/navigation";

import {
  chatService
} from "@/services/chat.service";

import {
  Message
} from "@/types/chat.types";

import ChatWindow from "@/components/chat/ChatWindow";
import ChatInput from "@/components/chat/ChatInput";
import TypingIndicator from "@/components/chat/TypingIndicator";
import {useRouter } from "next/navigation";

export default function ChatPage() {

  const params = useParams();
  const router = useRouter();

  const conversationId =
    params.conversationId as string;

  const [messages, setMessages] =
    useState<Message[]>([]);

  const [loading, setLoading] =
    useState(false);

  const loadMessages =
    async () => {

      try {

        const data =
          await chatService.getMessages(
            conversationId
          );

        setMessages(data);

      } catch (error) {

        console.error(error);
      }
    };

  useEffect(() => {

    if (conversationId) {
      loadMessages();
    }

  }, [conversationId]);

  const handleSend =
    async (message: string) => {

      try {

        setLoading(true);

        await chatService.sendMessage(
          conversationId,
          message
        );

        await loadMessages();

      } catch (error) {

        console.error(error);

      } finally {

        setLoading(false);
      }
    };

  return (
  <div className="h-screen bg-gray-50 flex flex-col">

    {/* Header */}
    <div className="bg-white border-b">

      <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">

        <div className="flex items-center gap-4">

          <button
            onClick={() =>
              router.push("/companions")
            }
            className="
              px-4
              py-2
              border
              rounded-xl
              hover:bg-gray-100
              transition
            "
          >
            ← Back
          </button>

          <div className="h-12 w-12 rounded-full bg-black text-white flex items-center justify-center font-bold">
            AI
          </div>

          <div>

            <h1 className="text-2xl font-bold text-gray-900">
              AI Companion Chat
            </h1>

            <p className="text-gray-500 text-sm">
              Personalized AI Assistant
            </p>

          </div>

        </div>

        <div className="flex items-center gap-2">

          <div className="h-3 w-3 rounded-full bg-green-500" />

          <span className="text-green-600 text-sm font-medium">
            Online
          </span>

        </div>

      </div>

    </div>

    {/* Messages Area */}
    <div className="flex-1 overflow-y-auto">

      <div className="max-w-5xl mx-auto px-6 py-8">

        {messages.length === 0 ? (

          <div className="h-full flex flex-col items-center justify-center text-center mt-24">

            <div className="text-7xl mb-6">
              🤖
            </div>

            <h2 className="text-4xl font-bold text-gray-900 mb-3">
              Start a Conversation
            </h2>

            <p className="text-gray-500 mb-10">
              Ask anything to your AI Companion
            </p>

          </div>

        ) : (

          <>
            <ChatWindow
              messages={messages}
            />

            {loading && (
              <TypingIndicator />
            )}
          </>

        )}

      </div>

    </div>

    {/* Input Area */}
    <div className="bg-white border-t">

      <div className="max-w-5xl mx-auto p-5">

        <div className="bg-gray-50 border rounded-2xl p-3 shadow-sm">

          <ChatInput
            loading={loading}
            onSend={handleSend}
          />

        </div>

      </div>

    </div>

  </div>
);
}