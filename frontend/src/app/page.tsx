"use client";

import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">

      {/* Background Glow */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-blue-500/20 blur-[150px]" />
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-500/20 blur-[150px]" />

      <div className="relative z-10 min-h-screen flex flex-col">

        {/* Navbar */}
        <nav className="flex items-center justify-between px-10 py-6">

          <h1 className="text-2xl font-bold text-white">
            AGIX
          </h1>

          <div className="flex gap-4">

            <button
              onClick={() =>
                router.push("/login")
              }
              className="
                text-white
                hover:text-blue-400
                transition
              "
            >
              Login
            </button>

            <button
              onClick={() =>
                router.push("/register")
              }
              className="
                bg-white
                text-black
                px-5
                py-2
                rounded-full
                font-semibold
                hover:scale-105
                transition
              "
            >
              Register
            </button>

          </div>

        </nav>

        {/* Hero Section */}
        <div className="flex-1 flex items-center justify-center px-6">

          <div className="max-w-6xl text-center">

            <h1 className="text-6xl md:text-8xl font-bold text-white leading-tight">

              Your Personal

              <span className="block bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                AI Companion
              </span>

            </h1>

            <p className="mt-8 text-xl text-gray-400 max-w-3xl mx-auto">
              Learn faster, stay productive,
              improve wellness, build better habits,
              and grow your career with intelligent
              AI companions designed for your goals.
            </p>

            <div className="flex justify-center gap-5 mt-12">

              <button
                onClick={() =>
                  router.push("/register")
                }
                className="
                  px-8
                  py-4
                  bg-white
                  text-black
                  rounded-xl
                  font-semibold
                  hover:scale-105
                  transition
                "
              >
                Get Started
              </button>

              <button
                onClick={() =>
                  router.push("/login")
                }
                className="
                  px-8
                  py-4
                  border
                  border-white/20
                  text-white
                  rounded-xl
                  hover:bg-white/10
                  transition
                "
              >
                Sign In
              </button>

            </div>

          </div>

        </div>

        {/* Features */}
        <div className="pb-16 px-8">

          <div className="max-w-7xl mx-auto grid md:grid-cols-5 gap-5">

            <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-3xl p-6">
              <h3 className="text-white font-bold text-xl mb-3">
                📚 Aria
              </h3>
              <p className="text-gray-400">
                Study Agent for learning,
                concepts and exam preparation.
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-3xl p-6">
              <h3 className="text-white font-bold text-xl mb-3">
                🧘 Noor
              </h3>
              <p className="text-gray-400">
                Wellness Agent for mindfulness,
                peace and emotional wellbeing.
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-3xl p-6">
              <h3 className="text-white font-bold text-xl mb-3">
                🎯 Rene
              </h3>
              <p className="text-gray-400">
                Life Coach Agent helping you
                achieve goals and build habits.
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-3xl p-6">
              <h3 className="text-white font-bold text-xl mb-3">
                💪 Max
              </h3>
              <p className="text-gray-400">
                Fitness Agent for workouts,
                nutrition and healthy habits.
              </p>
            </div>

            <div className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-3xl p-6">
              <h3 className="text-white font-bold text-xl mb-3">
                💼 Victor
              </h3>
              <p className="text-gray-400">
                Business Agent for startups,
                strategy and entrepreneurship.
              </p>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
}