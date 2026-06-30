"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  const companions = [
    {
      name: "Aria",
      role: "Study Companion",
      image: "/main/aria.png",
      description:
        "Your AI partner for learning, concepts and exam preparation.",
    },
    {
      name: "Noor",
      role: "Wellness Companion",
      image: "/main/noor.png",
      description:
        "Your guide to mindfulness, peace and emotional wellbeing.",
    },
    {
      name: "Rene",
      role: "Life Coach",
      image: "/main/rene.png",
      description:
        "Build habits, achieve goals and stay focused every day.",
    },
    {
      name: "Max",
      role: "Fitness Companion",
      image: "/main/max.png",
      description:
        "Personalized workouts, nutrition and healthy habit tracking.",
    },
    {
      name: "Victor",
      role: "Business Companion",
      image: "/main/victor.png",
      description:
        "Your advisor for strategy, growth and smarter decisions.",
    },
  ];

  return (
    <div className="min-h-screen bg-[#f8f8fc] overflow-hidden relative">
      {/* Background Glow */}
      <div className="absolute top-20 right-20 w-125 h-125 bg-violet-300/30 rounded-full blur-[120px]" />
      <div className="absolute bottom-0 left-0 w-100 h-100 bg-purple-200/30 rounded-full blur-[120px]" />

      <div className="relative z-10">
        {/* Navbar */}
        <nav className="max-w-7xl mx-auto px-8 py-8 flex items-center justify-between">
          <h1 className="text-4xl font-bold text-[#0B1230]">
            AGIX
          </h1>

          <div className="flex items-center gap-5">
            <button
              onClick={() => router.push("/login")}
              className="
                text-[#0B1230]
                font-medium
                hover:text-violet-600
                transition
              "
            >
              Login
            </button>

            <button
              onClick={() => router.push("/register")}
              className="
                px-6
                py-3
                rounded-full
                text-white
                bg-linear-to-r
                from-violet-600
                to-purple-500
                hover:scale-105
                transition
              "
            >
              Register
            </button>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="max-w-7xl mx-auto px-8 py-10">
          <div className="grid lg:grid-cols-2 gap-10 items-center">
            {/* Left */}
            <div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight text-[#0B1230]">
                Your Personal
                <span
                  className="
                  block
                  bg-linear-to-r
                  from-violet-600
                  to-purple-400
                  bg-clip-text
                  text-transparent
                "
                >
                  AI Companion
                </span>
              </h1>

              <p className="mt-8 text-xl text-slate-500 max-w-xl leading-relaxed">
                Learn faster, stay productive, improve wellness,
                build better habits, and grow your career with
                intelligent AI companions designed for your goals.
              </p>

              <div className="flex flex-wrap gap-5 mt-10">
                <button
                  onClick={() => router.push("/register")}
                  className="
                    px-8
                    py-4
                    rounded-2xl
                    text-white
                    font-semibold
                    bg-linear-to-r
                    from-violet-600
                    to-purple-500
                    hover:scale-105
                    transition
                  "
                >
                  Get Started →
                </button>

                <button
                  onClick={() => router.push("/login")}
                  className="
                    px-8
                    py-4
                    rounded-2xl
                    border-2
                    border-violet-300
                    text-violet-600
                    font-semibold
                    hover:bg-violet-50
                    transition
                  "
                >
                  Sign In
                </button>
              </div>

              <div className="flex flex-wrap gap-8 mt-10 text-slate-500">
                <div>🔒 Private & Secure</div>
                <div>✨ Personalized For You</div>
                <div>⚡ Always Learning</div>
              </div>
            </div>

            {/* Right */}
            <div className="relative flex justify-center items-center">
              <div
                className="
                  absolute
                  w-112.5
                  h-112.5
                  rounded-full
                  bg-linear-to-r
                  from-violet-300
                  to-purple-300
                  opacity-40
                "
              />

              <div className="relative flex justify-center">
                <div
                  className="
                    absolute
                    w-130
                    h-130
                    rounded-full
                    bg-linear-to-r
                    from-violet-300
                    to-purple-300
                    opacity-50
                    blur-sm
                  "
                />

                <Image
                  src="/main/mainlogo.png"
                  alt="AI Companion"
                  width={550}
                  height={550}
                  className="relative z-10 object-contain"
                  priority
                />

                <div className="absolute top-20 left-0 bg-white p-5 rounded-3xl shadow-lg w-40">
                  <p className="font-semibold">Learn smarter</p>
                  <p className="text-sm text-gray-500">
                    AI-powered study sessions
                  </p>
                </div>

                <div className="absolute top-18 right-0 bg-white p-5 rounded-3xl shadow-lg w-40">
                  <p className="font-semibold">Feel better</p>
                  <p className="text-sm text-gray-500">
                    Mindfulness support
                  </p>
                </div>

                <div className="absolute bottom-2 left-2 bg-white p-5 rounded-3xl shadow-lg w-40">
                  <p className="font-semibold">Achieve goals</p>
                  <p className="text-sm text-gray-500">
                    Personalized roadmaps
                  </p>
                </div>

                <div className="absolute bottom-2 right-0 bg-white p-5 rounded-3xl shadow-lg w-40">
                  <p className="font-semibold">Track progress</p>
                  <p className="text-sm text-gray-500">
                    Insights that drive growth
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Companion Cards Section */}
        <section className="max-w-7xl mx-auto px-8 py-20">
          <div className="text-center mb-14">
            <h2 className="text-4xl font-bold text-[#0B1230]">
              Meet Your AI Companions
            </h2>

            <p className="mt-4 text-slate-500 max-w-2xl mx-auto">
              Choose an AI companion tailored to your goals and get
              personalized guidance every day.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-6">
            {companions.map((companion) => (
              <div
                key={companion.name}
                className="
                  bg-white/80
                  backdrop-blur-md
                  rounded-[32px]
                  border
                  border-white
                  shadow-lg
                  overflow-hidden
                  relative
                  h-105
                  hover:-translate-y-2
                  transition-all
                  duration-300
                "
              >
                <div className="p-6 relative z-10">
                  <h3 className="text-2xl font-bold text-[#0B1230]">
                    {companion.name}
                  </h3>

                  <p className="text-sm font-medium text-violet-600">
                    {companion.role}
                  </p>

                  <p className="mt-4 text-sm text-slate-500">
                    {companion.description}
                  </p>
                </div>

                <Image
                  src={companion.image}
                  alt={companion.name}
                  width={400}
                  height={400}
                  className="
                    absolute
                    bottom-0
                    left-0
                    w-full
                    h-70
                    object-cover
                  "
                />

                <button
                  className="
                    absolute
                    bottom-5
                    right-5
                    w-12
                    h-12
                    rounded-full
                    bg-white
                    shadow-lg
                    text-xl
                    hover:bg-violet-600
                    hover:text-white
                    transition
                  "
                >
                  →
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}