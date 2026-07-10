import Cookies from "js-cookie";
import { api } from "@/lib/api";

export const tavusService = {
  async createSession(companionId: string) {
    const token = Cookies.get("token");

    const response = await api.post(
      `/tavus/session/${companionId}`,
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
      `/tavus/session/${conversationId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  },

  async endSession(conversationId: string) {
    const token = Cookies.get("token");

    const response = await api.post(
      `/tavus/session/${conversationId}/end`,
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  },
};