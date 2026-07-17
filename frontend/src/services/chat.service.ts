import { api } from "@/lib/api";

import {
  Message,
  ChatResponse,
} from "@/types/chat.types";

export interface ConversationDetails {
  id: string;
  companion_id: string;
  companion_name?: string;
}

export interface ChatRequest {
  conversation_id: string;
  message: string;
}

export const chatService = {

  async getMessages(
    conversationId: string
  ): Promise<Message[]> {

    const response =
      await api.get<Message[]>(
        `/chat/${conversationId}`
      );

    return response.data;
  },

  async sendMessage(
    conversationId: string,
    message: string
  ): Promise<ChatResponse> {

    const payload: ChatRequest = {
      conversation_id: conversationId,
      message,
    };

    const response =
      await api.post<ChatResponse>(
        "/chat",
        payload
      );

    return response.data;
  },

  async getConversationById(
    conversationId: string
  ): Promise<ConversationDetails> {

    const response =
      await api.get<ConversationDetails>(
        `/conversations/${conversationId}`
      );

    return response.data;
  },
};