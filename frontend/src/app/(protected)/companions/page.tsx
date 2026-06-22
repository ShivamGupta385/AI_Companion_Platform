"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import CompanionCard from "@/components/companion/CompanionCard";

import { companionService } from "@/services/companion.service";
import { conversationService } from "@/services/conversation.service";

import { Companion } from "@/types/companion.types";

export default function CompanionsPage() {
  const router = useRouter();

  const [companions, setCompanions] = useState<Companion[]>([]);

  useEffect(() => {
    const loadCompanions = async () => {
      try {
        const data =
          await companionService.getCompanions();

        setCompanions(data);
      } catch (error) {
        console.error(error);
      }
    };

    loadCompanions();
  }, []);

  const handleSelect = async (
    companion: Companion
  ) => {
    try {
      const conversation =
        await conversationService.createConversation(
          companion.id
        );

      router.push(
        `/chat/${conversation.id}`
      );
    } catch (error) {
      console.error(error);

      alert(
        "Failed to create conversation"
      );
    }
  };

  return (
    <div className="min-h-screen bg-[#F8F7FC]">

      <div className="w-full px-8 lg:px-12 py-8">

        {/* Badge */}

        <div
          className="
            inline-flex
            items-center
            gap-2
            px-5
            py-3
            rounded-full
            bg-violet-100
            text-violet-600
            font-medium
            mb-8
          "
        >
          ✨ AI Companions
        </div>

        {/* Hero Section */}

        <div
          className="
            flex
            flex-col
            lg:flex-row
            items-center
            justify-between
            gap-10
            mb-10
          "
        >
          <div className="flex-1">

            <h1
              className="
                text-[56px]
                lg:text-[72px]
                leading-none
                font-bold
                tracking-tight
                text-slate-900
              "
            >
              Choose Your{" "}
              <span className="text-violet-600">
                Companion
              </span>
            </h1>

            <p
              className="
                mt-6
                text-[18px]
                leading-8
                text-slate-500
                max-w-[720px]
              "
            >
              Select a specialized AI companion
              tailored to your goals, learning,
              wellness, fitness, business, and
              personal growth journey.
            </p>

          </div>

          <div className="hidden lg:block">
            <img
              src="/companion/robot.png"
              alt="robot"
              className="
                w-[360px]
                object-contain
              "
            />
          </div>

        </div>

        {/* Stats */}

        <div
          className="
            grid
            grid-cols-1
            md:grid-cols-3
            gap-6
            mb-10
          "
        >

          <div
            className="
              bg-white
              rounded-[28px]
              h-[120px]
              px-8
              flex
              flex-col
              justify-center
              shadow-sm
              border
              border-[#F0EEF7]
            "
          >
            <p className="text-slate-500">
              Available Companions
            </p>

            <h2
              className="
                text-4xl
                font-bold
                text-slate-900
                mt-2
              "
            >
              {companions.length}
            </h2>
          </div>

          <div
            className="
              bg-white
              rounded-[28px]
              h-[120px]
              px-8
              flex
              flex-col
              justify-center
              shadow-sm
              border
              border-[#F0EEF7]
            "
          >
            <p className="text-slate-500">
              Categories
            </p>

            <h2
              className="
                text-4xl
                font-bold
                text-slate-900
                mt-2
              "
            >
              5
            </h2>
          </div>

          <div
            className="
              bg-white
              rounded-[28px]
              h-[120px]
              px-8
              flex
              flex-col
              justify-center
              shadow-sm
              border
              border-[#F0EEF7]
            "
          >
            <p className="text-slate-500">
              Status
            </p>

            <h2
              className="
                text-4xl
                font-bold
                text-green-500
                mt-2
              "
            >
              Active
            </h2>
          </div>

        </div>

        {/* Companion Cards */}

        <div
          className="
            grid
            grid-cols-1
            lg:grid-cols-3
            gap-6
          "
        >
          {companions.map(
            (companion) => (
              <CompanionCard
                key={companion.id}
                companion={companion}
                onSelect={handleSelect}
              />
            )
          )}
        </div>

      </div>

    </div>
  );
}