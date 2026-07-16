"use client";

import React, { useState } from "react";
import { format, parseISO, startOfYear, endOfYear, eachDayOfInterval, getMonth, getDay, isSameDay } from "date-fns";

interface ContributionHeatmapProps {
  data: {
    date: string;
    duration_minutes: number;
    agents: string[];
    last_time?: string;
  }[];
}

export default function ContributionHeatmap({ data }: ContributionHeatmapProps) {
  const [mounted, setMounted] = useState(false);
  const [tooltipData, setTooltipData] = useState<{ x: number, y: number, content: string } | null>(null);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="w-full bg-white p-8 rounded-3xl shadow-sm border border-gray-100 flex flex-col relative min-h-[250px] items-center justify-center">
        <div className="w-8 h-8 border-4 border-violet-200 border-t-violet-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  // Generate all days in the current year
  const today = new Date();
  const start = startOfYear(today);
  const end = endOfYear(today);
  const allDays = eachDayOfInterval({ start, end });

  // Group days by month
  const months: { [key: number]: Date[] } = {};
  allDays.forEach(date => {
    const month = getMonth(date);
    if (!months[month]) months[month] = [];
    months[month].push(date);
  });

  const getLevelColor = (duration: number, hasConversation: boolean) => {
    if (duration > 60) return "#15803d"; // bg-green-700
    if (duration > 30) return "#16a34a"; // bg-green-600
    if (duration > 10) return "#22c55e"; // bg-green-500
    if (duration > 0 || hasConversation) return "#86efac"; // bg-green-300
    return "#f3f4f6"; // bg-gray-100
  };

  const handleMouseEnter = (e: React.MouseEvent, date: Date, stat: any) => {
    const rect = (e.target as HTMLElement).getBoundingClientRect();
    const count = stat ? (stat.duration_minutes === 0 ? 1 : stat.duration_minutes) : 0;
    
    let content = `${count} minutes on ${format(date, 'MMM do, yyyy')}`;
    if (stat && stat.agents && stat.agents.length > 0) {
      content = `Date: ${format(date, 'MMM do, yyyy')}\nDuration: ${count} min\nAgents: ${stat.agents.join(", ")}\nLast Active: ${stat.last_time || "N/A"}`;
    }

    setTooltipData({
      x: rect.left + rect.width / 2,
      y: rect.top - 10,
      content
    });
  };

  return (
    <div className="w-full bg-white p-8 rounded-3xl shadow-sm border border-gray-100 flex flex-col relative">
      <h3 className="text-xl font-bold text-gray-800 mb-6">Conversation Heatmap</h3>
      
      <div className="flex overflow-x-auto pb-4 gap-4">
        {Object.entries(months).map(([monthIdx, daysInMonth]) => {
          // Calculate padding to align the first day to the correct day of the week
          const firstDayOfWeek = getDay(daysInMonth[0]);
          const blankDays = Array(firstDayOfWeek).fill(null);
          
          return (
            <div key={monthIdx} className="flex flex-col gap-2">
              <span className="text-xs text-gray-500 mb-1">{format(daysInMonth[0], 'MMM')}</span>
              <div className="grid grid-rows-7 grid-flow-col gap-[6px]">
                {blankDays.map((_, i) => (
                  <div key={`blank-${i}`} className="w-[14px] h-[14px]"></div>
                ))}
                {daysInMonth.map((date, i) => {
                  const dateStr = format(date, 'yyyy-MM-dd');
                  const stat = data.find(d => d.date === dateStr);
                  const colorHex = getLevelColor(stat?.duration_minutes || 0, !!stat?.agents?.length);
                  
                  return (
                    <div
                      key={dateStr}
                      className={`w-[14px] h-[14px] rounded-[3px] transition-colors cursor-pointer hover:ring-2 hover:ring-offset-1 hover:ring-gray-300`}
                      style={{ backgroundColor: colorHex }}
                      onMouseEnter={(e) => handleMouseEnter(e, date, stat)}
                      onMouseLeave={() => setTooltipData(null)}
                    ></div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Custom Tooltip */}
      {tooltipData && (
        <div 
          className="fixed z-50 bg-gray-900 text-white text-xs p-3 rounded-lg shadow-xl pointer-events-none whitespace-pre-line leading-relaxed"
          style={{
            left: tooltipData.x,
            top: tooltipData.y,
            transform: 'translate(-50%, -100%)'
          }}
        >
          {tooltipData.content}
          {/* Tooltip arrow */}
          <div className="absolute left-1/2 -bottom-1 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
        </div>
      )}
    </div>
  );
}
