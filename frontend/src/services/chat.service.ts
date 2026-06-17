import Cookies from "js-cookie";

import { api } from "@/lib/api";

import {
  Message,
  ChatResponse,
} from "@/types/chat.types";

export const chatService = {

  async getMessages(
    conversationId: string
  ): Promise<Message[]> {

    const token =
      Cookies.get("token");

    const response =
      await api.get<Message[]>(
        `/chat/${conversationId}`,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );

    return response.data;
  },

  async sendMessage(
    conversationId: string,
    message: string
  ): Promise<ChatResponse> {

    const token =
      Cookies.get("token");

    const response =
      await api.post<ChatResponse>(
        "/chat",
        {
          conversation_id:
            conversationId,
          message,
        },
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );

    return response.data;
  },
};