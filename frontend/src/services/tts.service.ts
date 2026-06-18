import Cookies from "js-cookie";
import { api } from "@/lib/api";

export const ttsService = {

  async speak(text: string) {

    const token =
      Cookies.get("token");

    const response =
      await api.post(
        "/tts/speak",
        { text },
        {
          responseType: "blob",
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );

    return response.data;
  },
};