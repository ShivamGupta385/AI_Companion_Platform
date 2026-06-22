import Image from "next/image";

export default function DashboardHero() {
  return (
    <>
      <div className="mb-8">

        <div className="inline-flex rounded-full border border-violet-200 bg-white px-5 py-2 text-violet-600">
          ✨ AGIX AI Companion Platform
        </div>

        <div className="mt-6 grid grid-cols-2 gap-6">

          <div>
            <h1 className="text-7xl font-bold text-slate-900">
              Welcome Back 👋
            </h1>

            <p className="mt-4 max-w-xl text-2xl text-gray-500">
              Manage your onboarding profile,
              AI companions and conversations
              from one intelligent dashboard.
            </p>
          </div>

          <div>
            <Image
              src="/dashboard/hero.png"
              alt="Hero"
              width={700}
              height={400}
              className="w-full"
            />
          </div>

        </div>
      </div>

      {/* Stats */}

      <div className="grid grid-cols-3 gap-5">

        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <p>AI Companions</p>
          <h2 className="text-4xl font-bold">
            5
          </h2>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <p>Conversations</p>
          <h2 className="text-4xl font-bold">
            Active
          </h2>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <p>Status</p>
          <h2 className="text-4xl font-bold text-green-500">
            Online
          </h2>
        </div>

      </div>
    </>
  );
}