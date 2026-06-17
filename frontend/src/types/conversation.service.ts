import Cookies from "js-cookie";
import { api } from "@/lib/api";

import {
  Conversation,
  ConversationCreate,
} from "@/types/conversation.types";

export const conversationService = {
  async create(
    data: ConversationCreate
  ): Promise<Conversation> {

    const token =
      Cookies.get("token");

    const response =
      await api.post<Conversation>(
        "/conversations",
        data,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );

    return response.data;
  },

  async getAll() {

    const token =
      Cookies.get("token");

    const response =
      await api.get(
        "/conversations",
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );

    return response.data;
  },

  async getById(
    conversationId: string
  ) {

    const token =
      Cookies.get("token");

    const response =
      await api.get(
        `/conversations/${conversationId}`,
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