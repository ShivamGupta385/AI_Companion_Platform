"use client";

import { Play } from "lucide-react";

interface AvatarPlaceholderProps {
  onStart: () => void;
}

export default function AvatarPlaceholder({
  onStart,
}: AvatarPlaceholderProps) {
  return (
    <div className="w-full rounded-3xl border border-[#ECEAF4] bg-white p-4 shadow-sm">
      <div className="flex h-105 flex-col items-center justify-center rounded-2xl bg-slate-50">

        <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-violet-100 text-5xl">
          🤖
        </div>

        <h2 className="text-2xl font-bold text-slate-900">
          Avatar Offline
        </h2>

        <p className="mt-3 max-w-md text-center text-slate-500">
          No Tavus conversation has been started.
          <br />
          Click the button below whenever you want to test the avatar.
        </p>

        <button
          onClick={onStart}
          className="
            mt-8
            flex
            items-center
            gap-2
            rounded-2xl
            bg-linear-to-r
            from-violet-500
            to-purple-600
            px-6
            py-3
            text-white
            font-semibold
            shadow-lg
            hover:scale-105
            transition-all
          "
        >
          <Play size={18} />
          Start Avatar
        </button>
      </div>
    </div>
  );
}