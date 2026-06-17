import { api } from "@/lib/api";

import {
  RegisterRequest,
  LoginRequest,
  TokenResponse,
  User,
} from "@/types/auth.types";

export const authService = {
  async register(
    data: RegisterRequest
  ): Promise<User> {
    const response = await api.post<User>(
      "/auth/register",
      data
    );

    return response.data;
  },

  async login(
    data: LoginRequest
  ): Promise<TokenResponse> {
    const formData = new URLSearchParams();

    formData.append(
      "username",
      data.email
    );

    formData.append(
      "password",
      data.password
    );

    const response = await api.post<TokenResponse>(
      "/auth/login",
      formData,
      {
        headers: {
          "Content-Type":
            "application/x-www-form-urlencoded",
        },
      }
    );

    return response.data;
  },

  async getMe(
    token: string
  ): Promise<User> {
    const response = await api.get<User>(
      "/auth/me",
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  },
};