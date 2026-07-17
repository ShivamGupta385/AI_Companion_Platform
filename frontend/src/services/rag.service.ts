import Cookies from "js-cookie";
import { api } from "@/lib/api";

export const ragService = {
  async uploadDocument(
    file: File,
    companionId: string
  ) {
    const token = Cookies.get("token");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("companion_id", companionId);

    const response = await api.post(
      "/documents/upload",
      formData,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      }
    );

    return response.data;
  },
};