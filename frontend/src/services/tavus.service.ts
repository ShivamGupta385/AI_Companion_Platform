import Cookies from "js-cookie";
import { api } from "@/lib/api";

export const tavusService = {
  async createSession(companionId: string) {
    const token = Cookies.get("token");

    const response = await api.post(
      `/api/v1/tavus/session/${companionId}`,   // ✅ fixed path
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  },

  async getSession(conversationId: string) {
    const token = Cookies.get("token");

    const response = await api.get(
      `/api/v1/tavus/session/${conversationId}`,   // ✅ fixed path
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  },

  async sendMessage(conversationId: string, message: string) {
    const token = Cookies.get("token");

    const response = await api.post(
      `/api/v1/chat/`,   // ✅ fixed path
      {
        conversation_id: conversationId,
        message: message,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    // Response contains { response: string, tavus_video_url?: string }
    return response.data;
  }
};
