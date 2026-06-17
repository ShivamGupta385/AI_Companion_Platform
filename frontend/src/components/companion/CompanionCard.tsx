import { Companion } from "@/types/companion.types";

interface Props {
  companion: Companion;
  onSelect: (
    companion: Companion
  ) => void;
}

const icons: Record<string, string> = {
  Aria: "📚",
  Noor: "🧘",
  Rene: "🎯",
  Max: "💪",
  Victor: "💼",
};

export default function CompanionCard({
  companion,
  onSelect,
}: Props) {

  return (
    <div
      onClick={() =>
        onSelect(companion)
      }
      className="
        group
        cursor-pointer
        rounded-3xl
        border
        border-white/10
        bg-white/5
        backdrop-blur-xl
        p-6
        hover:border-purple-500/40
        hover:shadow-2xl
        hover:shadow-purple-500/20
        hover:-translate-y-2
        transition-all
        duration-300
      "
    >

      <div className="text-5xl mb-4">
        {icons[companion.name] ?? "🤖"}
      </div>

      <h2 className="text-2xl font-bold text-white mb-2">
        {companion.name}
      </h2>

      <p className="text-purple-300 mb-5">
        {companion.persona}
      </p>

      <div className="space-y-2 text-sm text-slate-400">

        {companion.name === "Aria" && (
          <>
            <p>✓ Study Planning</p>
            <p>✓ Concept Learning</p>
            <p>✓ Quiz Generation</p>
          </>
        )}

        {companion.name === "Noor" && (
          <>
            <p>✓ Meditation</p>
            <p>✓ Mindfulness</p>
            <p>✓ Emotional Wellness</p>
          </>
        )}

        {companion.name === "Rene" && (
          <>
            <p>✓ Goal Setting</p>
            <p>✓ Habit Building</p>
            <p>✓ Personal Growth</p>
          </>
        )}

        {companion.name === "Max" && (
          <>
            <p>✓ Workout Plans</p>
            <p>✓ Nutrition</p>
            <p>✓ Fitness Tracking</p>
          </>
        )}

        {companion.name === "Victor" && (
          <>
            <p>✓ Startup Guidance</p>
            <p>✓ Business Strategy</p>
            <p>✓ Productivity</p>
          </>
        )}

      </div>

      <button
        className="
          mt-6
          w-full
          rounded-xl
          bg-gradient-to-r
          from-purple-500
          to-blue-500
          py-3
          text-white
          font-semibold
          opacity-0
          group-hover:opacity-100
          transition
        "
      >
        Start Chat →
      </button>

    </div>
  );
}