import Cookies from "js-cookie";
import { api } from "@/lib/api";

export interface ConversationListItem {
  id: string;
  user_id: string;
  companion_id: string;
  companion_name: string;
  conversation_type: string;
  started_at: string;
  updated_at: string;
  last_message?: string | null;
  message_count: number;
}

export interface ConversationDetail {
  id: string;
  user_id: string;
  companion_id: string;
  companion_name: string;
  conversation_type: string;
  started_at: string;
  updated_at: string;
}

export const conversationService = {
  async createConversation(companionId: string) {
    const token = Cookies.get("token");

    const response = await api.post(
      "/conversations",
      {
        companion_id: companionId,
        conversation_type: "chat",
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  },

  async getConversations(): Promise<ConversationListItem[]> {
    const token = Cookies.get("token");

    const response = await api.get("/conversations", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  },

  async getConversation(
    conversationId: string
  ): Promise<ConversationDetail> {
    const token = Cookies.get("token");

    const response = await api.get(
      `/conversations/${conversationId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  },
};