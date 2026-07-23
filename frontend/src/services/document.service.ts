import Cookies from "js-cookie";

import { api } from "@/lib/api";

export interface Document {
  id: string;
  file_name: string;
  file_path: string;
  uploaded_at: string;
}

export const documentService = {

  async getDocuments(): Promise<Document[]> {

    const token =
      Cookies.get("token");

    console.log(
      "DOCUMENT TOKEN:",
      token
    );

    const response =
      await api.get(
        "/documents",
        {
          headers: {
            Authorization:
              `Bearer ${token}`
          }
        }
      );

    return response.data;
  },

  async deleteDocument(
    documentId: string
  ): Promise<void> {

    const token =
      Cookies.get("token");

    await api.delete(
      `/documents/${documentId}`,
      {
        headers: {
          Authorization:
            `Bearer ${token}`
        }
      }
    );
  }

};