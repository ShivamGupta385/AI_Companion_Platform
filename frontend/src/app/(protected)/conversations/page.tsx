"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { MessageSquare, Clock, Bot } from "lucide-react";

import {
  conversationService,
  ConversationListItem,
} from "@/services/conversation.service";

export default function ConversationsPage() {
  const router = useRouter();

  const [conversations, setConversations] = useState<
    ConversationListItem[]
  >([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadConversations = async () => {
      try {
        const data =
          await conversationService.getConversations();
        setConversations(data);
      } catch (error) {
        console.error(
          "Failed to load conversations:",
          error
        );
      } finally {
        setLoading(false);
      }
    };

    loadConversations();
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);

    return date.toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  };

  const openConversation = (
    conversationId: string
  ) => {
    router.push(`/chat/${conversationId}`);
  };

  return (
    <div className="min-h-screen bg-[#f7f4fb] p-6">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Conversations
          </h1>
          <p className="mt-2 text-gray-600">
            View all your past AI companion chats.
          </p>
        </div>

        {loading ? (
          <div className="rounded-2xl bg-white p-8 shadow-sm">
            <p className="text-gray-500">
              Loading conversations...
            </p>
          </div>
        ) : conversations.length === 0 ? (
          <div className="rounded-2xl bg-white p-8 shadow-sm">
            <p className="text-gray-500">
              No conversations found yet.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() =>
                  openConversation(conversation.id)
                }
                className="w-full rounded-2xl bg-white p-5 text-left shadow-sm transition hover:shadow-md hover:border-purple-300 border border-transparent"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-purple-100 text-purple-600">
                      <Bot className="h-6 w-6" />
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <h2 className="text-lg font-semibold text-gray-900">
                          {conversation.companion_name}
                        </h2>

                        <span className="rounded-full bg-purple-50 px-3 py-1 text-xs font-medium text-purple-700">
                          {conversation.conversation_type}
                        </span>
                      </div>

                      <p className="max-w-2xl truncate text-sm text-gray-600">
                        {conversation.last_message ||
                          "No messages yet."}
                      </p>

                      <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          <span>
                            Updated:{" "}
                            {formatDate(
                              conversation.updated_at
                            )}
                          </span>
                        </div>

                        <div className="flex items-center gap-1">
                          <MessageSquare className="h-4 w-4" />
                          <span>
                            {conversation.message_count} messages
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="text-sm font-medium text-purple-600">
                    Open →
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}