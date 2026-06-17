"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import { onboardingService } from "@/services/onboarding.service";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function OnboardingForm() {
  const router = useRouter();

  const [loading, setLoading] = useState(false);

  const [isUpdate, setIsUpdate] =
    useState(false);

  const [formData, setFormData] =
    useState({
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
      const data =
        await onboardingService.getMe();

      const baseline =
        data.baseline_data;

      setFormData({
        age: String(
          baseline.age || ""
        ),
        occupation:
          baseline.occupation || "",
        country:
          baseline.country || "",
        goals:
          baseline.goals || "",
        interests:
          baseline.interests || "",
      });

      setIsUpdate(true);

    } catch (error) {

      console.log(
        "No onboarding found"
      );

      setIsUpdate(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData({
      ...formData,
      [e.target.name]:
        e.target.value,
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
          occupation:
            formData.occupation,
          country:
            formData.country,
          goals:
            formData.goals,
          interests:
            formData.interests,
        },
      };

      if (isUpdate) {

        await onboardingService.update(
          payload
        );

      } else {

        await onboardingService.create(
          payload
        );
      }

      alert(
        isUpdate
          ? "Profile updated successfully"
          : "Profile created successfully"
      );

      router.replace(
        "/dashboard"
      );

    } catch (error) {

      console.error(error);

      alert(
        "Failed to save onboarding"
      );

    } finally {

      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4"
    >
      <Input
        name="age"
        placeholder="Age"
        value={formData.age}
        onChange={handleChange}
      />

      <Input
        name="occupation"
        placeholder="Occupation"
        value={formData.occupation}
        onChange={handleChange}
      />

      <Input
        name="country"
        placeholder="Country"
        value={formData.country}
        onChange={handleChange}
      />

      <Input
        name="goals"
        placeholder="Goals"
        value={formData.goals}
        onChange={handleChange}
      />

      <Input
        name="interests"
        placeholder="Interests"
        value={formData.interests}
        onChange={handleChange}
      />

      <Button
        type="submit"
        className="w-full"
        disabled={loading}
      >
        {loading
          ? "Saving..."
          : isUpdate
          ? "Update Profile"
          : "Create Profile"}
      </Button>
    </form>
  );
}