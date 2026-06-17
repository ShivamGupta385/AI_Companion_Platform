import Cookies from "js-cookie";

import { api } from "@/lib/api";

import {
  OnboardingRequest,
  OnboardingResponse,
} from "@/types/onboarding.types";

export const onboardingService = {
  async create(
    data: OnboardingRequest
  ): Promise<OnboardingResponse> {

    const token = Cookies.get("token");

    const response =
      await api.post<OnboardingResponse>(
        "/user-onboarding/",
        data,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

    return response.data;
  },

  async getMe(): Promise<OnboardingResponse> {

    const token = Cookies.get("token");

    const response =
      await api.get<OnboardingResponse>(
        "/user-onboarding/me",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

    return response.data;
  },

  async update(
    data: OnboardingRequest
  ): Promise<OnboardingResponse> {

    const token = Cookies.get("token");

    const response =
      await api.put<OnboardingResponse>(
        "/user-onboarding/me",
        data,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

    return response.data;
  },
};