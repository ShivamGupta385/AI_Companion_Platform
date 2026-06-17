"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";

export default function DashboardPage() {
  const router = useRouter();

  const { logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-slate-950 relative overflow-hidden">

      {/* Background Glow */}
      <div className="absolute top-0 left-0 h-96 w-96 bg-blue-500/20 rounded-full blur-[150px]" />
      <div className="absolute bottom-0 right-0 h-96 w-96 bg-purple-500/20 rounded-full blur-[150px]" />

      <div className="relative z-10 p-8 md:p-12">

        {/* Hero Section */}
        <div className="mb-12">

          <div className="inline-flex px-4 py-2 rounded-full border border-blue-500/20 bg-blue-500/10 text-blue-400">
            🚀 AGIX AI Companion Platform
          </div>

          <h1 className="mt-6 text-6xl font-bold text-white">
            Welcome Back 👋
          </h1>

          <p className="mt-4 text-lg text-slate-400 max-w-2xl">
            Manage your onboarding profile,
            AI companions and conversations
            from one intelligent dashboard.
          </p>

        </div>

        {/* Stats Section */}
        <div className="grid md:grid-cols-3 gap-6 mb-10">

          <div className="rounded-3xl bg-white/5 backdrop-blur-xl border border-white/10 p-6">
            <p className="text-slate-400">
              AI Companions
            </p>

            <h2 className="text-4xl font-bold text-white mt-2">
              5
            </h2>
          </div>

          <div className="rounded-3xl bg-white/5 backdrop-blur-xl border border-white/10 p-6">
            <p className="text-slate-400">
              Conversations
            </p>

            <h2 className="text-4xl font-bold text-white mt-2">
              Active
            </h2>
          </div>

          <div className="rounded-3xl bg-white/5 backdrop-blur-xl border border-white/10 p-6">
            <p className="text-slate-400">
              Status
            </p>

            <h2 className="text-4xl font-bold text-green-400 mt-2">
              Online
            </h2>
          </div>

        </div>

        {/* Feature Cards */}
        <div className="grid gap-8 md:grid-cols-3">

          {/* Onboarding */}
          <div
            className="
              rounded-3xl
              bg-white/5
              backdrop-blur-xl
              border
              border-white/10
              p-8
              hover:border-blue-500/30
              hover:scale-[1.02]
              transition-all
            "
          >
            <div className="text-5xl mb-5">
              👤
            </div>

            <h2 className="text-2xl font-bold text-white mb-3">
              User Onboarding
            </h2>

            <p className="text-slate-400 mb-6">
              Complete or update your
              personal profile information.
            </p>

            <button
              onClick={() =>
                router.push("/onboarding")
              }
              className="
                px-5
                py-3
                rounded-xl
                font-semibold
                bg-gradient-to-r
                from-blue-500
                to-cyan-500
                text-white
                hover:opacity-90
                transition
              "
            >
              Open Onboarding
            </button>
          </div>

          {/* Companions */}
          <div
            className="
              rounded-3xl
              bg-white/5
              backdrop-blur-xl
              border
              border-white/10
              p-8
              hover:border-purple-500/30
              hover:scale-[1.02]
              transition-all
            "
          >
            <div className="text-5xl mb-5">
              🤖
            </div>

            <h2 className="text-2xl font-bold text-white mb-3">
              AI Companions
            </h2>

            <p className="text-slate-400 mb-6">
              Explore and chat with
              specialized AI companions.
            </p>

            <button
              onClick={() =>
                router.push("/companions")
              }
              className="
                px-5
                py-3
                rounded-xl
                font-semibold
                bg-gradient-to-r
                from-purple-500
                to-pink-500
                text-white
                hover:opacity-90
                transition
              "
            >
              View Companions
            </button>
          </div>

          {/* Logout */}
          <div
            className="
              rounded-3xl
              bg-white/5
              backdrop-blur-xl
              border
              border-white/10
              p-8
              hover:border-red-500/30
              hover:scale-[1.02]
              transition-all
            "
          >
            <div className="text-5xl mb-5">
              🚪
            </div>

            <h2 className="text-2xl font-bold text-white mb-3">
              Logout
            </h2>

            <p className="text-slate-400 mb-6">
              Securely sign out from
              your AGIX account.
            </p>

            <button
              onClick={handleLogout}
              className="
                px-5
                py-3
                rounded-xl
                font-semibold
                bg-gradient-to-r
                from-red-500
                to-orange-500
                text-white
                hover:opacity-90
                transition
              "
            >
              Logout
            </button>
          </div>

        </div>

      </div>
    </div>
  );
}