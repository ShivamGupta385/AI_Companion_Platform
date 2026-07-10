"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Calendar,
  Globe,
  Heart,
  BookOpen,
  Smile,
  MessageCircle,
  Target,
  Mountain,
  MessageSquare,
} from "lucide-react";

import { onboardingService } from "@/services/onboarding.service";

export default function OnboardingForm() {
  const router = useRouter();

  const [loading, setLoading] = useState(false);
  const [isUpdate, setIsUpdate] = useState(false);

  const [formData, setFormData] = useState({
    nickname: "",
    age: "",
    current_focus: "",
    preferred_tone: "",
    goals: "",
    interests: "",
    favorite_topics: "",
    current_challenge: "",
    country: "",
  });

  useEffect(() => {
    loadOnboarding();
  }, []);

  const loadOnboarding = async () => {
    try {
      const data = await onboardingService.getMe();

      const baseline = data.baseline_data;

      setFormData({
        nickname: baseline.nickname || "",
        age: String(baseline.age || ""),
        current_focus: baseline.current_focus || "",
        preferred_tone: baseline.preferred_tone || "",
        goals: baseline.goals || "",
        interests: baseline.interests || "",
        favorite_topics: baseline.favorite_topics || "",
        current_challenge: baseline.current_challenge || "",
        country: baseline.country || "",
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
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
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
          nickname: formData.nickname,
          age: Number(formData.age),
          current_focus: formData.current_focus,
          preferred_tone: formData.preferred_tone,
          goals: formData.goals,
          interests: formData.interests,
          favorite_topics: formData.favorite_topics,
          current_challenge: formData.current_challenge,
          country: formData.country,
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
  const labelStyle = "block text-sm font-semibold text-gray-700 mb-1 ml-1";

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* SECTION 1: THE BASICS (MANDATORY) */}
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">The Basics</h2>
          <p className="text-sm text-gray-500 mb-4">Required so Aria knows how to talk to you.</p>
        </div>

        <div>
          <label className={labelStyle}>Nickname <span className="text-red-500">*</span></label>
          <div className="relative">
            <Smile className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
            <input
              required
              name="nickname"
              placeholder="What should Aria call you?"
              value={formData.nickname}
              onChange={handleChange}
              className={inputStyle}
            />
          </div>
        </div>

        <div>
          <label className={labelStyle}>Age <span className="text-red-500">*</span></label>
          <div className="relative">
            <Calendar className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
            <input
              required
              type="number"
              name="age"
              placeholder="Your age"
              value={formData.age}
              onChange={handleChange}
              className={inputStyle}
            />
          </div>
        </div>

        <div>
          <label className={labelStyle}>Primary Focus <span className="text-red-500">*</span></label>
          <div className="relative">
            <Target className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
            <input
              required
              name="current_focus"
              placeholder="e.g., High School, College, Working"
              value={formData.current_focus}
              onChange={handleChange}
              className={inputStyle}
            />
          </div>
        </div>

        <div>
          <label className={labelStyle}>Preferred Tone <span className="text-red-500">*</span></label>
          <div className="relative">
            <MessageCircle className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
            <select
              required
              name="preferred_tone"
              value={formData.preferred_tone}
              onChange={handleChange}
              className={`${inputStyle} appearance-none bg-white`}
            >
              <option value="" disabled>How should Aria talk to you?</option>
              <option value="Chill & Fun">Chill & Fun</option>
              <option value="Supportive & Sweet">Supportive & Sweet</option>
              <option value="Smart & Direct">Smart & Direct</option>
            </select>
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200 my-8"></div>

      {/* SECTION 2: THE DEEP DIVE (OPTIONAL) */}
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">The Deep Dive</h2>
          <p className="text-sm text-gray-500 mb-4">Optional context to make your companion much smarter.</p>
        </div>

        <div>
          <label className={labelStyle}>Favorite Topics (Optional)</label>
          <div className="relative">
            <MessageSquare className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
            <input
              name="favorite_topics"
              placeholder="What could you talk about for hours?"
              value={formData.favorite_topics}
              onChange={handleChange}
              className={inputStyle}
            />
          </div>
        </div>

        <div>
          <label className={labelStyle}>Interests & Hobbies (Optional)</label>
          <div className="relative">
            <BookOpen className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
            <input
              name="interests"
              placeholder="What do you do for fun?"
              value={formData.interests}
              onChange={handleChange}
              className={inputStyle}
            />
          </div>
        </div>

        <div>
          <label className={labelStyle}>Goals (Optional)</label>
          <div className="relative">
            <Heart className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
            <input
              name="goals"
              placeholder="What do you want to achieve?"
              value={formData.goals}
              onChange={handleChange}
              className={inputStyle}
            />
          </div>
        </div>

        <div>
          <label className={labelStyle}>Current Challenge (Optional)</label>
          <div className="relative">
            <Mountain className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
            <input
              name="current_challenge"
              placeholder="What is a struggle you are facing right now?"
              value={formData.current_challenge}
              onChange={handleChange}
              className={inputStyle}
            />
          </div>
        </div>

        <div>
          <label className={labelStyle}>Location (Optional)</label>
          <div className="relative">
            <Globe className="absolute left-5 top-1/2 -translate-y-1/2 text-violet-500" />
            <input
              name="country"
              placeholder="Where are you from?"
              value={formData.country}
              onChange={handleChange}
              className={inputStyle}
            />
          </div>
        </div>
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
          mt-6
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