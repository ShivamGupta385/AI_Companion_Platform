import Image from "next/image";
import RegisterForm from "@/components/auth/RegisterForm";
import Link from "next/link";

export default function RegisterPage() {
  return (
    <div className="min-h-screen bg-[#f8f7ff]">

      <div className="grid min-h-screen lg:grid-cols-2">

        {/* LEFT SIDE */}

        <div className="relative hidden lg:flex items-center justify-center overflow-hidden">

          <div className="absolute left-10 top-10 text-5xl font-black">
            AGIX
          </div>

          <div className="absolute left-175 top-10 rounded-3xl bg-white p-5 shadow-xl">
            <p className="text-lg">
              Let's build your
            </p>
            <p className="font-semibold text-violet-600">
              AI companion
            </p>
            <p>experience ✨</p>
          </div>

          <div className="absolute h-162.5 w-162.5 rounded-full bg-violet-200 opacity-30" />

          <Image
            src="/register/register.png"
            alt="AI Assistant"
            width={700}
            height={700}
            className="relative z-10 object-contain"
            priority
          />
        </div>

        {/* RIGHT SIDE */}

        <div className="flex items-center justify-center p-8">

          <div className="w-full max-w-2xl rounded-[40px] border border-white/40 bg-white/80 p-10 shadow-2xl backdrop-blur-xl">

            <div className="mb-8 text-center">

              <div className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-full bg-linear-to-r from-violet-500 to-purple-300 text-4xl text-white">
                🤖
              </div>

              <h1 className="text-6xl font-bold text-slate-900">
                Create Account
              </h1>

              <p className="mt-4 text-lg text-gray-500">
                Join us and get started today
              </p>

              <div className="mx-auto mt-4 h-1 w-14 rounded-full bg-violet-500" />
            </div>

            <RegisterForm />

            <div className="my-8 flex items-center">
              <div className="h-px flex-1 bg-gray-200" />
              <span className="px-4 text-gray-500">
                or continue with
              </span>
              <div className="h-px flex-1 bg-gray-200" />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <button className="rounded-xl border p-3">
                Google
              </button>

              <button className="rounded-xl border p-3">
                Microsoft
              </button>

              <button className="rounded-xl border p-3">
                Apple
              </button>
            </div>

            <p className="mt-8 text-center text-gray-600">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-semibold text-violet-600 transition hover:text-violet-700 hover:underline"
            >
              Sign In →
            </Link>
          </p>

          </div>

        </div>

      </div>

    </div>
  );
}