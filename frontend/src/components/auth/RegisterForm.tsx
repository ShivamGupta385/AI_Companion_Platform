"use client";

import { useAuthStore } from "@/store/auth-store";
import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  User,
  AtSign,
  Mail,
  Lock,
  Eye,
  EyeOff,
} from "lucide-react";

import { authService } from "@/services/auth.service";

export default function RegisterForm() {
  const router = useRouter();
  const { setToken } = useAuthStore();

  const [showPassword, setShowPassword] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [formData, setFormData] =
    useState({
      full_name: "",
      username: "",
      email: "",
      password: "",
    });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (
    e: React.FormEvent
  ) => {
    e.preventDefault();

    try {
      setLoading(true);

      await authService.register(formData);

      // Automatically log the user in
      const loginResponse = await authService.login({
        email: formData.email,
        password: formData.password,
      });

      // Save the token
      setToken(loginResponse.access_token);

      // Redirect new users to onboarding
      router.replace("/onboarding");
    } catch (error: any) {
      console.error(error);
      const errorMessage = error.response?.data?.detail || "Registration Failed";
      alert(errorMessage);
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
        <User className="absolute left-4 top-1/2 -translate-y-1/2 text-violet-500" />
        <input
          name="full_name"
          placeholder="Full Name"
          value={formData.full_name}
          onChange={handleChange}
          className="w-full rounded-xl border border-gray-200 py-4 pl-12 pr-4"
        />
      </div>

      <div className="relative">
        <AtSign className="absolute left-4 top-1/2 -translate-y-1/2 text-violet-500" />
        <input
          name="username"
          placeholder="Username"
          value={formData.username}
          onChange={handleChange}
          className="w-full rounded-xl border border-gray-200 py-4 pl-12 pr-4"
        />
      </div>

      <div className="relative">
        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-violet-500" />
        <input
          type="email"
          name="email"
          placeholder="Email"
          value={formData.email}
          onChange={handleChange}
          className="w-full rounded-xl border border-gray-200 py-4 pl-12 pr-4"
        />
      </div>

      <div className="relative">
        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-violet-500" />

        <input
          type={
            showPassword
              ? "text"
              : "password"
          }
          name="password"
          placeholder="Password"
          value={formData.password}
          onChange={handleChange}
          className="w-full rounded-xl border border-gray-200 py-4 pl-12 pr-12"
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

      <button
        type="submit"
        disabled={loading}
        className="h-14 w-full rounded-xl bg-linear-to-r from-violet-600 to-purple-400 text-lg font-semibold text-white shadow-lg"
      >
        {loading
          ? "Creating..."
          : "Create Account →"}
      </button>
    </form>
  );
}