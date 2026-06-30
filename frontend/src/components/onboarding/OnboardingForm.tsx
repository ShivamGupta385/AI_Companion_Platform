"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Calendar,
  GraduationCap,
  Globe,
  Heart,
  BookOpen,
} from "lucide-react";

import { onboardingService } from "@/services/onboarding.service";

export default function OnboardingForm() {
  const router = useRouter();

  const [loading, setLoading] = useState(false);
  const [isUpdate, setIsUpdate] = useState(false);

  const [formData, setFormData] = useState({
    age: "",
    occupation: "",
    country: "",
    goals: "",
    interests: "",
  });

  useEffect(() => {
    loadOnboarding();
  }, []);

  const loadOnboarding = async () => {
    try {
      const data = await onboardingService.getMe();

      const baseline = data.baseline_data;

      setFormData({
        age: String(baseline.age || ""),
        occupation: baseline.occupation || "",
        country: baseline.country || "",
        goals: baseline.goals || "",
        interests: baseline.interests || "",
      });

      setIsUpdate(true);

    } catch (error: any) {

      if (error.response?.status === 404) {
        // New user (no onboarding yet)
        setIsUpdate(false);
      } else {
        console.error(error);
        alert("Unable to load your profile.");
      }

    }
  };

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

      const payload = {
        baseline_data: {
          age: Number(formData.age),
          occupation: formData.occupation,
          country: formData.country,
          goals: formData.goals,
          interests: formData.interests,
        },
      };

      if (isUpdate) {
        await onboardingService.update(payload);
      } else {
        await onboardingService.create(payload);
      }

      router.replace("/dashboard");

    } catch (error) {
      console.error(error);
      alert("Unable to save your profile.");
    } finally {
      setLoading(false);
    }
  };

  const inputStyle =
    "w-full rounded-2xl border border-slate-200 py-4 pl-14 pr-4 outline-none focus:border-violet-500";

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5"
    >
      <div className="relative">
        <Calendar className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
        <input
          name="age"
          placeholder="Age"
          value={formData.age}
          onChange={handleChange}
          className={inputStyle}
        />
      </div>

      <div className="relative">
        <GraduationCap className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
        <input
          name="occupation"
          placeholder="Occupation"
          value={formData.occupation}
          onChange={handleChange}
          className={inputStyle}
        />
      </div>

      <div className="relative">
        <Globe className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
        <input
          name="country"
          placeholder="Country"
          value={formData.country}
          onChange={handleChange}
          className={inputStyle}
        />
      </div>

      <div className="relative">
        <Heart className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
        <input
          name="goals"
          placeholder="Goals"
          value={formData.goals}
          onChange={handleChange}
          className={inputStyle}
        />
      </div>

      <div className="relative">
        <BookOpen className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
        <input
          name="interests"
          placeholder="Interests"
          value={formData.interests}
          onChange={handleChange}
          className={inputStyle}
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="
          w-full
          rounded-2xl
          bg-linear-to-r
          from-violet-600
          to-purple-400
          py-4
          text-lg
          font-semibold
          text-white
        "
      >
        {loading
          ? "Saving..."
          : isUpdate
          ? "Update Profile →"
          : "Create Profile →"}
      </button>
    </form>
  );
}