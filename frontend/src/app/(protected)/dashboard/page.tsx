"use client";

import { useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";

import {
  Bell,
  Bot,
  MessageCircle,
  Radio,
  LogOut,
} from "lucide-react";

import { useAuthStore } from "@/store/auth-store";

export default function DashboardPage() {
  const router = useRouter();

  const {
    logout,
    user,
    fetchCurrentUser,
  } = useAuthStore();

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  const displayName =
    user?.full_name ||
    user?.username ||
    "User";

  return (
    <div className="min-h-screen bg-[#F8F7FF]">
      <main className="max-w-7xl mx-auto px-8 py-6">
        {/* HEADER */}
        <div className="flex justify-between items-center mb-8">
          {/* Logo */}
          <div className="relative">
            <h1 className="text-5xl font-black tracking-tight text-black">
              AGIX
            </h1>

            <div className="absolute -top-2 right-2 text-violet-500 text-xl">
              ✦
            </div>
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-4">
            <button
              className="
                h-14
                w-14
                rounded-full
                bg-white
                shadow-sm
                flex
                items-center
                justify-center
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
                className="rounded-full"
              />

              <span className="font-medium">
                {displayName}
              </span>
            </div>
          </div>
        </div>

        {/* HERO SECTION */}
        <div className="grid lg:grid-cols-2 gap-8 items-center">
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
                text-violet-600
                font-medium
              "
            >
              ✨ AGIX AI Companion Platform
            </div>

            <h1
              className="
                mt-6
                text-6xl
                font-bold
                text-slate-900
              "
            >
              Welcome Back 👋
            </h1>

            <p
              className="
                mt-4
                max-w-xl
                text-xl
                text-slate-500
              "
            >
              Manage your onboarding profile,
              AI companions and conversations
              from one intelligent dashboard.
            </p>
          </div>

          <div className="flex justify-center">
            <Image
              src="/dashboard/main.png"
              alt="hero"
              width={650}
              height={350}
              className="object-contain"
              priority
            />
          </div>
        </div>

        {/* STATS */}
        <div className="grid md:grid-cols-3 gap-5 mt-8">
          {/* AI Companions */}
          <div className="bg-white rounded-3xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div
                className="
                  h-14
                  w-14
                  rounded-full
                  bg-violet-100
                  flex
                  items-center
                  justify-center
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
          <div className="bg-white rounded-3xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div
                className="
                  h-14
                  w-14
                  rounded-full
                  bg-cyan-100
                  flex
                  items-center
                  justify-center
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
          <div className="bg-white rounded-3xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div
                className="
                  h-14
                  w-14
                  rounded-full
                  bg-green-100
                  flex
                  items-center
                  justify-center
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
        <div className="grid lg:grid-cols-3 gap-6 mt-8">
          {/* ONBOARDING */}
          <div className="bg-white rounded-[32px] p-6 shadow-sm flex flex-col h-[560px]">
            <div className="h-[220px] flex items-center justify-center">
              <Image
                src="/dashboard/onboarding.png"
                alt="onboarding"
                width={320}
                height={220}
                className="object-contain"
              />
            </div>

            <h2 className="mt-4 text-3xl font-semibold text-slate-900">
              User Insights
            </h2>

            <p className="mt-3 text-slate-500 flex-grow">
              Complete or update your personal profile information.
            </p>

            <button
              onClick={() => router.push("/onboarding")}
              className="
                mt-6
                w-full
                rounded-2xl
                bg-gradient-to-r
                from-violet-600
                to-purple-400
                py-4
                text-white
                font-semibold
              "
            >
              See Details →
            </button>
          </div>

          {/* COMPANIONS */}
          <div className="bg-white rounded-[32px] p-6 shadow-sm flex flex-col h-[560px]">
            <div className="h-[220px] flex items-center justify-center">
              <Image
                src="/dashboard/robot.png"
                alt="companion"
                width={320}
                height={220}
                className="object-contain"
              />
            </div>

            <h2 className="mt-4 text-3xl font-semibold text-slate-900">
              AI Companions
            </h2>

            <p className="mt-3 text-slate-500 flex-grow">
              Explore and chat with specialized AI companions.
            </p>

            <button
              onClick={() => router.push("/companions")}
              className="
                mt-6
                w-full
                rounded-2xl
                bg-gradient-to-r
                from-violet-600
                to-purple-400
                py-4
                text-white
                font-semibold
              "
            >
              View Companions →
            </button>
          </div>

          {/* LOGOUT */}
          <div className="bg-white rounded-[32px] p-6 shadow-sm flex flex-col h-[560px]">
            <div className="h-[220px] flex items-center justify-center">
              <Image
                src="/dashboard/logout.png"
                alt="Logout"
                width={320}
                height={220}
                className="object-contain"
              />
            </div>

            <h2 className="mt-4 text-3xl font-semibold text-slate-900">
              Logout
            </h2>

            <p className="mt-3 text-slate-500 flex-grow">
              Securely sign out from your AGIX account.
            </p>

            <button
              onClick={handleLogout}
              className="
                mt-6
                w-full
                rounded-2xl
                bg-gradient-to-r
                from-orange-500
                to-red-500
                py-4
                text-white
                font-semibold
                flex
                items-center
                justify-center
                gap-2
              "
            >
              <LogOut size={18} />
              Logout
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}