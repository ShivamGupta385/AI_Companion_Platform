"use client";

import { useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";

import {
  Bell,
  Bot,
  MessageCircle,
  Radio,
} from "lucide-react";

import { useAuthStore } from "@/store/auth-store";

export default function DashboardPage() {
  const router = useRouter();

  const { user, fetchCurrentUser } = useAuthStore();

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const displayName =
    user?.full_name ||
    user?.username ||
    "User";

  return (
    <div className="min-h-screen bg-[#F8F7FF]">
      <main className="mx-auto max-w-7xl px-6 py-6 lg:px-8">
        {/* HEADER */}
        <div className="mb-8 flex items-center justify-between">
          {/* Logo */}
          <div className="relative">
            <h1 className="text-5xl font-black tracking-tight text-black">
              AGIX
            </h1>

            <div className="absolute -right-2 -top-2 text-xl text-violet-500">
              ✦
            </div>
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-4">
            <button
              className="
                flex
                h-14
                w-14
                items-center
                justify-center
                rounded-full
                bg-white
                shadow-sm
              "
            >
              <Bell size={20} />
            </button>

            <div
              className="
                flex
                items-center
                gap-3
                rounded-full
                bg-white
                px-4
                py-2
                shadow-sm
              "
            >
              <Image
                src="/dashboard/robot.png"
                alt="user"
                width={42}
                height={42}
                className="rounded-full object-cover"
              />

              <span className="font-medium text-slate-800">
                {displayName}
              </span>
            </div>
          </div>
        </div>

        {/* HERO SECTION */}
        <div className="grid items-center gap-10 lg:grid-cols-2">
          {/* Left Content */}
          <div>
            <div
              className="
                inline-flex
                items-center
                gap-2
                rounded-full
                border
                border-violet-200
                bg-white
                px-5
                py-2
                font-medium
                text-violet-600
                shadow-sm
              "
            >
              ✨ AGIX AI Companion Platform
            </div>

            <h1 className="mt-6 text-5xl font-bold leading-tight text-slate-900 lg:text-6xl">
              Welcome Back 👋
            </h1>

            <p className="mt-4 max-w-xl text-lg leading-8 text-slate-500 lg:text-xl">
              Manage your onboarding profile, AI companions,
              shared documents, and conversations from one
              intelligent dashboard.
            </p>
          </div>

          {/* Right Hero Image */}
          <div className="flex justify-center lg:justify-end">
            <div className="relative w-full max-w-[560px]">
              <Image
                src="/dashboard/main.png"
                alt="hero"
                width={560}
                height={360}
                priority
                className="h-auto w-full object-contain"
              />
            </div>
          </div>
        </div>

        {/* STATS */}
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {/* AI Companions */}
          <div className="rounded-3xl bg-white p-6 shadow-sm transition hover:shadow-md">
            <div className="flex items-center gap-4">
              <div
                className="
                  flex
                  h-14
                  w-14
                  items-center
                  justify-center
                  rounded-full
                  bg-violet-100
                "
              >
                <Bot className="text-violet-600" />
              </div>

              <div>
                <p className="text-slate-500">
                  AI Companions
                </p>

                <h3 className="text-3xl font-bold text-slate-900">
                  5
                </h3>
              </div>
            </div>
          </div>

          {/* Conversations */}
          <div className="rounded-3xl bg-white p-6 shadow-sm transition hover:shadow-md">
            <div className="flex items-center gap-4">
              <div
                className="
                  flex
                  h-14
                  w-14
                  items-center
                  justify-center
                  rounded-full
                  bg-cyan-100
                "
              >
                <MessageCircle className="text-cyan-600" />
              </div>

              <div>
                <p className="text-slate-500">
                  Conversations
                </p>

                <h3 className="text-3xl font-bold text-slate-900">
                  Active
                </h3>
              </div>
            </div>
          </div>

          {/* Status */}
          <div className="rounded-3xl bg-white p-6 shadow-sm transition hover:shadow-md">
            <div className="flex items-center gap-4">
              <div
                className="
                  flex
                  h-14
                  w-14
                  items-center
                  justify-center
                  rounded-full
                  bg-green-100
                "
              >
                <Radio className="text-green-600" />
              </div>

              <div>
                <p className="text-slate-500">
                  Status
                </p>

                <h3 className="text-3xl font-bold text-green-500">
                  Online
                </h3>
              </div>
            </div>
          </div>
        </div>

        {/* FEATURE CARDS */}
        <div className="mt-10 grid gap-6 lg:grid-cols-3">
          {/* USER INSIGHTS */}
          <div className="group flex min-h-[500px] flex-col rounded-[32px] bg-white p-6 shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-xl">
            <div className="flex h-[220px] items-center justify-center rounded-3xl bg-gradient-to-br from-violet-50 to-purple-100 p-6">
              <Image
                src="/dashboard/onboarding.png"
                alt="User Insights"
                width={870}
                height={870}
                className="h-auto w-auto max-h-[180px] object-contain drop-shadow-md transition duration-300 group-hover:scale-105"
              />
            </div>

            <h2 className="mt-6 text-3xl font-semibold text-slate-900">
              User Insights
            </h2>

            <p className="mt-3 flex-grow leading-7 text-slate-500">
              Complete or update your personal profile information,
              preferences, and onboarding details to personalize
              your AGIX experience.
            </p>

            <button
              onClick={() => router.push("/onboarding")}
              className="mt-6 w-full rounded-2xl bg-gradient-to-r from-violet-600 to-purple-400 py-4 font-semibold text-white shadow-md transition hover:opacity-90"
            >
              See Details →
            </button>
          </div>

          {/* AI COMPANIONS */}
          <div className="group flex min-h-[500px] flex-col rounded-[32px] bg-white p-6 shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-xl">
            <div className="flex h-[220px] items-center justify-center rounded-3xl bg-gradient-to-br from-violet-50 to-purple-100 p-6">
              <Image
                src="/dashboard/robot.png"
                alt="AI Companions"
                width={220}
                height={170}
                className="h-auto w-auto max-h-[180px] object-contain drop-shadow-md transition duration-300 group-hover:scale-105"
              />
            </div>

            <h2 className="mt-6 text-3xl font-semibold text-slate-900">
              AI Companions
            </h2>

            <p className="mt-3 flex-grow leading-7 text-slate-500">
              Explore and chat with specialized AI companions built
              to assist with productivity, learning, workflows,
              and intelligent conversations.
            </p>

            <button
              onClick={() => router.push("/companions")}
              className="mt-6 w-full rounded-2xl bg-gradient-to-r from-violet-600 to-purple-400 py-4 font-semibold text-white shadow-md transition hover:opacity-90"
            >
              View Companions →
            </button>
          </div>

          {/* DOCUMENTS SHARED */}
          <div className="group flex min-h-[500px] flex-col rounded-[32px] bg-white p-6 shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-xl">
            <div className="flex h-[220px] items-center justify-center rounded-3xl bg-gradient-to-br from-violet-50 to-purple-100 p-6">
              <Image
                src="/dashboard/brain.png"
                alt="Documents Shared"
                width={220}
                height={170}
                className="h-auto w-auto max-h-[180px] object-contain drop-shadow-md transition duration-300 group-hover:scale-105"
              />
            </div>

            <h2 className="mt-6 text-3xl font-semibold text-slate-900">
              Documents Shared
            </h2>

            <p className="mt-3 flex-grow leading-7 text-slate-500">
              Upload, manage, and inspect documents shared with AGIX
              for RAG, memory, and document-based conversations
              across your AI workflows.
            </p>

            <button
              onClick={() => router.push("/documents")}
              className="mt-6 w-full rounded-2xl bg-gradient-to-r from-violet-600 to-purple-400 py-4 font-semibold text-white shadow-md transition hover:opacity-90"
            >
              View Documents →
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}