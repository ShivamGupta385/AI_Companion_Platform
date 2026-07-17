import Cookies from "js-cookie";
import { api } from "@/lib/api";

export interface Document {
  id: string;
  user_id: string;
  companion_id?: string | null;
  companion_name?: string | null;
  file_name: string;
  file_path: string;
  uploaded_at: string;
}

export const documentService = {
  async getDocuments(): Promise<Document[]> {
    const token = Cookies.get("token");

    const response = await api.get("/documents", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  },

  async deleteDocument(documentId: string): Promise<void> {
    const token = Cookies.get("token");

    await api.delete(`/documents/${documentId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  },
};