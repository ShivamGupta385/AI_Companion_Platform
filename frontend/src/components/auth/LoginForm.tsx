"use client";

import { onboardingService } from "@/services/onboarding.service";
import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
} from "lucide-react";

import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth-store";

export default function LoginForm() {
  const router = useRouter();
  const { setToken } = useAuthStore();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [showPassword, setShowPassword] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const handleSubmit = async (
    e: React.FormEvent
  ) => {
    e.preventDefault();

    try {
      setLoading(true);

      const response =
        await authService.login({
          email,
          password,
        });

      setToken(response.access_token);

      try {
        await onboardingService.getMe();

        // Onboarding already exists
        router.replace("/dashboard");
      } catch (error: any) {
        // If onboarding is not found, send new users there
        if (error?.response?.status === 404) {
          router.replace("/onboarding");
        } else {
          console.error(error);
          alert("Unable to verify onboarding status.");
        }
      }
    } catch (error) {
      console.error(error);

      alert(
        "Invalid credentials"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5"
    >
      <div className="relative">
        <Mail
          className="absolute left-4 top-1/2 -translate-y-1/2 text-violet-500"
          size={18}
        />

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) =>
            setEmail(e.target.value)
          }
          className="w-full rounded-xl border border-gray-200 bg-white py-4 pl-12 pr-4 outline-none transition focus:border-violet-500"
        />
      </div>

      <div className="relative">
        <Lock
          className="absolute left-4 top-1/2 -translate-y-1/2 text-violet-500"
          size={18}
        />

        <input
          type={
            showPassword
              ? "text"
              : "password"
          }
          placeholder="Password"
          value={password}
          onChange={(e) =>
            setPassword(
              e.target.value
            )
          }
          className="w-full rounded-xl border border-gray-200 bg-white py-4 pl-12 pr-12 outline-none transition focus:border-violet-500"
        />

        <button
          type="button"
          onClick={() =>
            setShowPassword(
              !showPassword
            )
          }
          className="absolute right-4 top-1/2 -translate-y-1/2"
        >
          {showPassword ? (
            <EyeOff size={18} />
          ) : (
            <Eye size={18} />
          )}
        </button>
      </div>

      <div className="flex items-center justify-between text-sm">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            className="accent-violet-600"
          />
          Remember me
        </label>

        <button
          type="button"
          className="text-violet-600 hover:underline"
        >
          Forgot password?
        </button>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="h-14 w-full rounded-xl bg-linear-to-r from-violet-600 to-purple-400 text-lg font-semibold text-white shadow-lg transition hover:scale-[1.02]"
      >
        {loading
          ? "Signing In..."
          : "Login →"}
      </button>
    </form>
  );
}