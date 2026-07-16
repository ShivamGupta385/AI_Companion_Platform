"use client";

import React from "react";
import { CalendarDays, Flame, Activity } from "lucide-react";

interface StatCardsProps {
  totalDays: number;
  longestStreak: number;
  currentStreak: number;
}

export default function StatCards({ totalDays, longestStreak, currentStreak }: StatCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 w-full">
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center gap-6 transition-all hover:shadow-md">
        <div className="w-14 h-14 rounded-2xl bg-violet-100 flex items-center justify-center text-violet-600 shrink-0">
          <CalendarDays size={28} />
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">Total Days Active</p>
          <p className="text-3xl font-black text-gray-900">{totalDays}</p>
        </div>
      </div>
      
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center gap-6 transition-all hover:shadow-md">
        <div className="w-14 h-14 rounded-2xl bg-amber-100 flex items-center justify-center text-amber-500 shrink-0">
          <Activity size={28} />
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">Longest Streak</p>
          <p className="text-3xl font-black text-gray-900">{longestStreak}</p>
        </div>
      </div>

      <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex items-center gap-6 transition-all hover:shadow-md">
        <div className="w-14 h-14 rounded-2xl bg-rose-100 flex items-center justify-center text-rose-500 shrink-0">
          <Flame size={28} />
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">Current Streak</p>
          <p className="text-3xl font-black text-gray-900">{currentStreak}</p>
        </div>
      </div>
    </div>
  );
}
