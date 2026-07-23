import Cookies from "js-cookie";
import { api } from "@/lib/api";

export const ragService = {

  async uploadDocument(
    file: File
  ) {

    const token =
      Cookies.get("token");

    const formData =
      new FormData();

    formData.append(
      "file",
      file
    );

    const response =
      await api.post(
        "/documents/upload",
        formData,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
            "Content-Type":
              "multipart/form-data",
          },
        }
      );

    return response.data;
  },
};