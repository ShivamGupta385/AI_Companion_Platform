import LoginForm from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-white">

      {/* Soft Background Effects */}
      <div className="absolute top-0 left-0 h-96 w-96 rounded-full bg-blue-100 blur-3xl opacity-50" />
      <div className="absolute bottom-0 right-0 h-96 w-96 rounded-full bg-purple-100 blur-3xl opacity-50" />

      {/* Grid Pattern */}
      <div
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage:
            "linear-gradient(rgba(0,0,0,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,.05) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* Content */}
      <div className="relative z-10 flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-md rounded-3xl border border-gray-200 bg-white p-8 shadow-xl">

          <div className="mb-8 text-center">
            <h1 className="text-4xl font-bold text-gray-900">
              Welcome Back
            </h1>
            <p className="mt-3 text-gray-500">
              Sign in to continue
            </p>
          </div>

          <LoginForm />

        </div>
      </div>
    </div>
  );
}