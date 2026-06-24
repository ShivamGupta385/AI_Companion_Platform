import Cookies from "js-cookie";
import { api } from "@/lib/api";

export interface LiveAvatarSessionResponse {
  sessionToken: string;
}

export const liveAvatarService = {
  async createSession(): Promise<LiveAvatarSessionResponse> {
    const token = Cookies.get("token");

    const response = await api.post<LiveAvatarSessionResponse>(
      "/liveavatar/session",
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