import Image from "next/image";
import OnboardingForm from "../../../components/onboarding/OnboardingForm";


export default function OnboardingPage() {
  return (
    <div className="flex min-h-screen bg-[#F8F7FF]">

      

      <main className="flex-1 flex items-center justify-center p-8">

        <div
          className="
            w-full
            max-w-6xl
            rounded-[36px]
            overflow-hidden
            bg-white
            shadow-xl
            grid
            lg:grid-cols-2
          "
        >
          {/* LEFT PANEL */}

          <div className="relative bg-linear-to-br from-white to-violet-50 p-10">

            {/* Decorative Shapes */}

            <div className="absolute top-0 left-10 h-40 w-40 rounded-b-full bg-violet-500/40" />

            <div className="absolute top-20 left-16 h-52 w-52 rounded-full bg-violet-200/40" />

            <div className="absolute bottom-32 right-10 h-40 w-40 rounded-full bg-cyan-200/50" />

            {/* Hero Image */}

            <div className="relative z-10 flex justify-center">
              <Image
                src="/onboarding/useronboarding.png"
                alt="Onboarding"
                width={520}
                height={520}
                className="object-contain"
                priority
              />
            </div>

            {/* Personalization Card */}

            <div
              className="
                mt-6
                rounded-3xl
                bg-white
                p-6
                shadow-md
                flex
                items-center
                gap-4
              "
            >
              <div
                className="
                  h-16
                  w-16
                  rounded-2xl
                  bg-linear-to-r
                  from-violet-600
                  to-purple-400
                  flex
                  items-center
                  justify-center
                  text-white
                  text-2xl
                "
              >
                ✨
              </div>

              <div>
                <h3 className="font-bold text-violet-600 text-lg">
                  Personalize your experience
                </h3>

                <p className="text-slate-500">
                  Help us understand you better so we can
                  recommend the perfect AI companions.
                </p>
              </div>
            </div>

          </div>

          {/* RIGHT PANEL */}

          <div className="p-10 flex items-center">

            <div className="w-full">

              <div className="mb-8">

                <div
                  className="
                    mb-5
                    h-20
                    w-20
                    rounded-full
                    bg-white
                    shadow-md
                    flex
                    items-center
                    justify-center
                    text-4xl
                  "
                >
                  👋
                </div>

                <h1 className="text-6xl font-bold text-slate-900">
                  User Insights
                </h1>

                <p className="mt-4 text-xl text-slate-500">
                  Complete your profile information to
                  personalize your AGIX experience.
                </p>

                <div className="mt-4 h-1 w-20 rounded-full bg-violet-500" />

              </div>

              <OnboardingForm />

              <p className="mt-6 text-sm text-slate-500">
                🔒 Your information is secure and will never
                be shared.
              </p>

            </div>

          </div>

        </div>

      </main>

    </div>
  );
}