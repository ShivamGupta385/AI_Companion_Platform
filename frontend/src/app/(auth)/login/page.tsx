import LoginForm from "@/components/auth/LoginForm";
import Image from "next/image";
import Link from "next/link";

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-[#f8f7ff]">

      <div className="grid min-h-screen lg:grid-cols-2">

        {/* LEFT SIDE */}

        <div className="relative hidden lg:flex items-center justify-center overflow-hidden">

          <div className="absolute left-20 top-0 h-72 w-72 rounded-b-full bg-gradient-to-b from-violet-300 to-violet-500 opacity-70" />

          <div className="absolute top-20 right-28 h-40 w-40 rounded-full bg-cyan-300 opacity-60" />

          <div className="absolute left-10 top-10 text-5xl font-black tracking-wider">
            AGIX
          </div>

          <Image
            src="/login/login.png"
            alt="AI Girl"
            width={700}
            height={700}
            className="relative z-10 object-contain"
            priority
          />
        </div>

        {/* RIGHT SIDE */}

        <div className="flex items-center justify-center p-8">

          <div className="w-full max-w-xl rounded-[40px] border border-white/50 bg-white/80 p-10 shadow-2xl backdrop-blur-xl">

            <div className="mb-10 text-center">

              <div className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-r from-violet-500 to-purple-300 text-3xl text-white">
                🤖
              </div>

              <h1 className="text-6xl font-bold text-slate-900">
                Welcome Back
              </h1>

              <p className="mt-4 text-lg text-slate-500">
                Sign in to continue your AI journey
              </p>

              <div className="mx-auto mt-4 h-1 w-16 rounded-full bg-violet-500" />
            </div>

            <LoginForm />

            <div className="my-8 flex items-center">
              <div className="h-px flex-1 bg-gray-200" />
              <span className="px-4 text-gray-500">
                or continue with
              </span>
              <div className="h-px flex-1 bg-gray-200" />
            </div>

            <div className="grid grid-cols-3 gap-4">

              <button className="rounded-xl border p-3 font-semibold">
                Google
              </button>

              <button className="rounded-xl border p-3 font-semibold">
                Microsoft
              </button>

              <button className="rounded-xl border p-3 font-semibold">
                GitHub
              </button>

            </div>

            <Link
              href="/register"
              className="mt-8 block text-center"
            >
              <span className="text-gray-600">
                Don't have an account?{" "}
              </span>
              <span className="font-semibold text-violet-600 hover:underline">
                Create one →
              </span>
            </Link>

          </div>

        </div>

      </div>

    </div>
  );
}