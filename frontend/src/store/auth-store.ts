import { create } from "zustand";
import Cookies from "js-cookie";
import { api } from "@/lib/api";

interface UserProfile {
  id: string;
  full_name: string | null;
  username: string | null;
  email: string;
  profile_image_url?: string | null;
  subscription_plan?: string | null;
  is_active?: boolean;
}

interface AuthState {
  token: string | null;
  user: UserProfile | null;

  setToken: (token: string) => void;
  setUser: (user: UserProfile | null) => void;
  fetchCurrentUser: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: Cookies.get("token") || null,
  user: null,

  setToken: (token) => {
    Cookies.set("token", token, {
      expires: 7,
      sameSite: "strict",
    });

    set({ token });
  },

  setUser: (user) => {
    set({ user });
  },

  fetchCurrentUser: async () => {
    try {
      const token = Cookies.get("token");

      if (!token) {
        set({ user: null });
        return;
      }

      const response = await api.get("/users/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      set({ user: response.data });
    } catch (error) {
      console.error("Failed to fetch current user:", error);
      set({ user: null });
    }
  },

  logout: () => {
    Cookies.remove("token");

    set({
      token: null,
      user: null,
    });
  },
}));