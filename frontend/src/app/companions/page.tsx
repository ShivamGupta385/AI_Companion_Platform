"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import CompanionCard from "@/components/companion/CompanionCard";

import { companionService } from "@/services/companion.service";
import { conversationService } from "@/services/conversation.service";

import { Companion } from "@/types/companion.types";

export default function CompanionsPage() {

  const router = useRouter();

  const [
    companions,
    setCompanions,
  ] = useState<Companion[]>([]);

  useEffect(() => {

    const loadCompanions =
      async () => {

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

  const handleSelect =
    async (
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
    <div className="min-h-screen bg-slate-950 relative overflow-hidden">

      {/* Background Glow */}
      <div className="absolute top-0 left-0 h-96 w-96 bg-blue-500/20 rounded-full blur-[150px]" />
      <div className="absolute bottom-0 right-0 h-96 w-96 bg-purple-500/20 rounded-full blur-[150px]" />

      <div className="relative z-10 p-8 md:p-12">

        {/* Header */}
        <div className="mb-12">

          <div className="inline-flex px-4 py-2 rounded-full border border-purple-500/20 bg-purple-500/10 text-purple-400">
            🤖 AI Companions
          </div>

          <h1 className="mt-6 text-6xl font-bold text-white">
            Choose Your Companion
          </h1>

          <p className="mt-4 text-lg text-slate-400 max-w-3xl">
            Select a specialized AI companion
            tailored to your goals, learning,
            wellness, fitness, business,
            and personal growth journey.
          </p>

        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">

          <div className="rounded-3xl bg-white/5 backdrop-blur-xl border border-white/10 p-6">
            <p className="text-slate-400">
              Available Companions
            </p>

            <h2 className="text-4xl font-bold text-white mt-2">
              {companions.length}
            </h2>
          </div>

          <div className="rounded-3xl bg-white/5 backdrop-blur-xl border border-white/10 p-6">
            <p className="text-slate-400">
              Categories
            </p>

            <h2 className="text-4xl font-bold text-white mt-2">
              5
            </h2>
          </div>

          <div className="rounded-3xl bg-white/5 backdrop-blur-xl border border-white/10 p-6">
            <p className="text-slate-400">
              Status
            </p>

            <h2 className="text-4xl font-bold text-green-400 mt-2">
              Active
            </h2>
          </div>

        </div>

        {/* Companion Cards */}
        <div
          className="
            grid
            gap-6
            md:grid-cols-2
            xl:grid-cols-3
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