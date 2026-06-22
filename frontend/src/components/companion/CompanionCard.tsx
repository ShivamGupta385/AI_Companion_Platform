import { Companion } from "@/types/companion.types";

interface Props {
  companion: Companion;
  onSelect: (companion: Companion) => void;
}

const companionData = {
  Aria: {
    image: "/companion/aria.png",
    role: "Study Agent",
    color: "from-violet-500 to-purple-500",
    features: [
      "Study Planning",
      "Concept Learning",
      "Quiz Generation",
    ],
  },

  Noor: {
    image: "/companion/noor.png",
    role: "Wellness Agent",
    color: "from-teal-400 to-cyan-500",
    features: [
      "Meditation",
      "Mindfulness",
      "Emotional Wellness",
    ],
  },

  Rene: {
    image: "/companion/rene.png",
    role: "Life Coach Agent",
    color: "from-purple-500 to-pink-500",
    features: [
      "Goal Setting",
      "Habit Building",
      "Personal Growth",
    ],
  },

  Max: {
    image: "/companion/max.png",
    role: "Fitness Agent",
    color: "from-orange-400 to-orange-600",
    features: [
      "Workout Plans",
      "Nutrition",
      "Fitness Tracking",
    ],
  },

  Victor: {
    image: "/companion/victor.png",
    role: "Business Agent",
    color: "from-violet-500 to-purple-500",
    features: [
      "Startup Guidance",
      "Business Strategy",
      "Productivity",
    ],
  },
};

export default function CompanionCard({
  companion,
  onSelect,
}: Props) {
  const data =
    companionData[
      companion.name as keyof typeof companionData
    ];

  return (
    <div
      onClick={() => onSelect(companion)}
      className="
      bg-white
      rounded-[30px]
      overflow-hidden
      border
      border-gray-100
      hover:shadow-2xl
      hover:-translate-y-2
      transition-all
      duration-300
      cursor-pointer
      "
    >
      <div className="grid grid-cols-2 h-full">

        <div className="relative bg-gradient-to-br from-violet-50 to-white flex items-center justify-center p-6">
          <img
            src={data.image}
            alt={companion.name}
            className="h-72 object-contain"
          />
        </div>

        <div className="p-6 flex flex-col justify-between">

          <div>

            <h2 className="text-4xl font-bold text-slate-900">
              {companion.name}
            </h2>

            <p className="text-sm font-semibold text-violet-600 mt-1">
              {data.role}
            </p>

            <div className="mt-5 space-y-3">
              {data.features.map((feature) => (
                <p
                  key={feature}
                  className="text-slate-500"
                >
                  ✓ {feature}
                </p>
              ))}
            </div>
          </div>

          <button
            className={`
            mt-6
            rounded-xl
            py-3
            text-white
            font-semibold
            bg-gradient-to-r
            ${data.color}
            `}
          >
            Start Chat →
          </button>

        </div>

      </div>
    </div>
  );
}