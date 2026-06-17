import Cookies from "js-cookie";

import { api } from "@/lib/api";

import { Companion } from "@/types/companion.types";

export const companionService = {
  async getCompanions(): Promise<
    Companion[]
  > {
    const token =
      Cookies.get("token");

    const response =
      await api.get<
        Companion[]
      >(
        "/companions",
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );

    return response.data;
  },

  async getCompanion(
    id: string
  ): Promise<Companion> {

    const token =
      Cookies.get("token");

    const response =
      await api.get<
        Companion
      >(
        `/companions/${id}`,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );

    return response.data;
  },
};