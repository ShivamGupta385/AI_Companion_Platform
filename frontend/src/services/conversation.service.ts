import Cookies from "js-cookie";
import { api } from "@/lib/api";

export const conversationService = {

  async createConversation(
    companionId: string
  ) {

    const token =
      Cookies.get("token");

    const response =
      await api.post(
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
};