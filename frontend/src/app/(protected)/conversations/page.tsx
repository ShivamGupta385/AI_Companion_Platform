"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  MessageSquare,
  Clock,
  Bot,
  Sparkles,
  Activity,
  MessagesSquare,
  Trash2,
  X, // 🆕 Added X icon for modal close
} from "lucide-react";

import {
  conversationService,
  ConversationListItem,
} from "@/services/conversation.service";

export default function ConversationsPage() {
  const router = useRouter();

  const [conversations, setConversations] = useState<ConversationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  
  // 🆕 Custom Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<ConversationListItem | null>(null);

  useEffect(() => {
    const loadConversations = async () => {
      try {
        const data = await conversationService.getConversations();
        setConversations(data);
      } catch (error) {
        console.error("Failed to load conversations:", error);
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

  const openConversation = (conversationId: string) => {
    router.push(`/chat/${conversationId}`);
  };

  // 🆕 UPDATED: Open modal instead of browser confirm
  const handleDeleteClick = (e: React.MouseEvent, conversation: ConversationListItem) => {
    e.stopPropagation();
    setConversationToDelete(conversation);
    setShowDeleteModal(true);
  };

  // 🆕 UPDATED: Actual delete logic
  const confirmDelete = async () => {
    if (!conversationToDelete) return;

    setDeletingId(conversationToDelete.id);
    setShowDeleteModal(false); // Close modal immediately

    try {
      await conversationService.deleteConversation(conversationToDelete.id);
      setConversations((prev) => prev.filter((c) => c.id !== conversationToDelete.id));
    } catch (error) {
      console.error("Failed to delete conversation:", error);
      alert("Failed to delete conversation. Please try again.");
    } finally {
      setDeletingId(null);
      setConversationToDelete(null);
    }
  };

  const totalMessages = conversations.reduce(
    (sum, conversation) => sum + (conversation.message_count || 0),
    0
  );

  return (
    <div className="min-h-screen bg-[#F8F7FC]">
      {/* 🆕 CUSTOM DELETE MODAL */}
      {showDeleteModal && conversationToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-3xl bg-white p-8 shadow-2xl">
            {/* Icon */}
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
              <Trash2 className="h-8 w-8 text-red-600" />
            </div>
            
            {/* Text */}
            <h3 className="mt-6 text-center text-xl font-bold text-slate-900">
              Delete Conversation?
            </h3>
            <p className="mt-3 text-center text-sm leading-6 text-slate-500">
              Are you sure you want to delete your chat with{" "}
              <span className="font-semibold text-slate-700">{conversationToDelete.companion_name}</span>? 
              This will permanently remove all messages and cannot be undone.
            </p>

            {/* Buttons */}
            <div className="mt-8 flex gap-4">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setConversationToDelete(null);
                }}
                className="flex-1 rounded-2xl border border-slate-200 bg-white px-6 py-3.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="flex-1 rounded-2xl bg-red-600 px-6 py-3.5 text-sm font-semibold text-white transition hover:bg-red-700"
              >
                Yes, Delete
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="mx-auto max-w-7xl px-6 py-8 lg:px-10">
        {/* PAGE HEADER */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 rounded-full bg-violet-100 px-5 py-2.5 text-sm font-medium text-violet-700">
            <Sparkles className="h-4 w-4" />
            AI Conversations
          </div>

          <div className="mt-6 grid items-center gap-8 lg:grid-cols-2">
            <div>
              <h1 className="text-5xl font-bold tracking-tight text-slate-900 lg:text-6xl">
                Your{" "}
                <span className="bg-gradient-to-r from-violet-600 to-purple-500 bg-clip-text text-transparent">
                  Conversations
                </span>
              </h1>

              <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-500">
                View, revisit, and continue your past AI companion chats.
                Every conversation keeps context, companion history, and
                message continuity in one place.
              </p>
            </div>

            <div className="hidden lg:flex justify-center">
              <div className="flex h-[260px] w-full max-w-[420px] items-center justify-center rounded-[32px] bg-gradient-to-br from-violet-50 to-purple-100 shadow-inner">
                <Bot className="h-24 w-24 text-violet-500" />
              </div>
            </div>
          </div>
        </div>

        {/* STATS */}
        <div className="mb-10 grid gap-6 md:grid-cols-3">
          <div className="rounded-[28px] bg-white p-6 shadow-sm ring-1 ring-[#F0EEF7] transition hover:-translate-y-1 hover:shadow-md">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-100">
                <MessagesSquare className="h-7 w-7 text-violet-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total Conversations</p>
                <h3 className="mt-1 text-3xl font-bold text-slate-900">
                  {loading ? "..." : conversations.length}
                </h3>
              </div>
            </div>
          </div>

          <div className="rounded-[28px] bg-white p-6 shadow-sm ring-1 ring-[#F0EEF7] transition hover:-translate-y-1 hover:shadow-md">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-100">
                <MessageSquare className="h-7 w-7 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total Messages</p>
                <h3 className="mt-1 text-3xl font-bold text-slate-900">
                  {loading ? "..." : totalMessages}
                </h3>
              </div>
            </div>
          </div>

          <div className="rounded-[28px] bg-white p-6 shadow-sm ring-1 ring-[#F0EEF7] transition hover:-translate-y-1 hover:shadow-md">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100">
                <Activity className="h-7 w-7 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Session Status</p>
                <h3 className="mt-1 text-3xl font-bold text-emerald-500">Active</h3>
              </div>
            </div>
          </div>
        </div>

        {/* CONVERSATION LIST SECTION */}
        <div className="rounded-[32px] bg-white p-6 shadow-sm ring-1 ring-[#F0EEF7] lg:p-8">
          <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Conversation History</h2>
              <p className="mt-1 text-sm text-slate-500">
                Open any chat to continue where you left off.
              </p>
            </div>

            <div className="text-sm text-slate-500">
              {loading
                ? "Loading..."
                : `${conversations.length} conversation${conversations.length !== 1 ? "s" : ""} found`}
            </div>
          </div>

          {loading ? (
            <div className="grid gap-4">
              {[1, 2, 3].map((item) => (
                <div
                  key={item}
                  className="animate-pulse rounded-[28px] border border-slate-200 bg-slate-50 p-6"
                >
                  <div className="flex items-start gap-4">
                    <div className="h-14 w-14 rounded-2xl bg-slate-200" />
                    <div className="flex-1">
                      <div className="h-5 w-48 rounded bg-slate-200" />
                      <div className="mt-3 h-4 w-3/4 rounded bg-slate-200" />
                      <div className="mt-4 flex gap-3">
                        <div className="h-8 w-32 rounded-full bg-slate-200" />
                        <div className="h-8 w-28 rounded-full bg-slate-200" />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : conversations.length === 0 ? (
            <div className="flex min-h-[280px] flex-col items-center justify-center rounded-[28px] border border-dashed border-slate-300 bg-slate-50 px-6 text-center">
              <div className="mb-4 rounded-full bg-white p-4 shadow-sm">
                <MessageSquare className="h-8 w-8 text-violet-500" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900">No conversations found yet</h3>
              <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
                Once you start chatting with your AI companions, your conversations will appear here so you can continue them anytime.
              </p>
            </div>
          ) : (
            <div className="space-y-5">
              {conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  onClick={() => openConversation(conversation.id)}
                  className="group w-full rounded-[30px] border border-[#ECEAF4] bg-white p-6 text-left shadow-sm transition duration-300 hover:-translate-y-1 hover:border-violet-200 hover:shadow-lg cursor-pointer"
                >
                  <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                    {/* LEFT CONTENT */}
                    <div className="flex min-w-0 flex-1 items-start gap-4">
                      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-100 to-purple-100 text-violet-600">
                        <Bot className="h-7 w-7" />
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-3">
                          <h3 className="text-xl font-semibold text-slate-900">
                            {conversation.companion_name}
                          </h3>
                          <span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">
                            {conversation.conversation_type}
                          </span>
                        </div>

                        <p className="mt-3 line-clamp-2 max-w-3xl text-sm leading-7 text-slate-500">
                          {conversation.last_message || "No messages yet."}
                        </p>

                        <div className="mt-5 flex flex-wrap gap-3">
                          <div className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-4 py-2 text-xs font-medium text-slate-600">
                            <Clock className="h-4 w-4" />
                            Updated: {formatDate(conversation.updated_at)}
                          </div>
                          <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-4 py-2 text-xs font-medium text-blue-700">
                            <MessageSquare className="h-4 w-4" />
                            {conversation.message_count} messages
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* RIGHT CTA + DELETE BUTTON */}
                    <div className="flex items-center justify-end gap-3 lg:min-w-[220px]">
                      
                      <button
                        onClick={(e) => handleDeleteClick(e, conversation)}
                        disabled={deletingId === conversation.id}
                        className="inline-flex items-center gap-2 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-600 opacity-0 transition-all duration-200 group-hover:opacity-100 hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Trash2 className="h-4 w-4" />
                        {deletingId === conversation.id ? "Deleting..." : "Delete"}
                      </button>

                      <div className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600 to-purple-500 px-5 py-3 text-sm font-semibold text-white shadow-sm transition group-hover:shadow-md">
                        Open Chat
                        <span>→</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}