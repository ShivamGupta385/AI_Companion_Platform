import { api } from "@/lib/api";

export const heygenService = {

  async createSession() {

    console.log(
      "BASE URL:",
      process.env.NEXT_PUBLIC_API_URL
    );

    try {

      const response =
        await api.post(
          "/heygen/video"
        );

      return response.data;

    } catch (error: any) {

      console.log(
        "REQUEST URL:",
        error.config?.baseURL +
        error.config?.url
      );

      console.log(
        "STATUS:",
        error.response?.status
      );

      console.log(
        "DATA:",
        error.response?.data
      );

      throw error;
    }
  }

};