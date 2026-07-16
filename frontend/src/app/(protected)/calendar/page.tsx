"use client";

import React, { useEffect, useState } from "react";
import ContributionHeatmap from "@/components/analytics/ContributionHeatmap";
import StatCards from "@/components/analytics/StatCards";
import { api } from "@/lib/api";

interface HeatmapData {
  date: string;
  duration_minutes: number;
  agents: string[];
}

interface AnalyticsResponse {
  total_days_active: number;
  longest_streak: number;
  current_streak: number;
  heatmap: HeatmapData[];
}

export default function CalendarPage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        // Assume axios instance handles auth interceptors correctly
        const response = await api.get("/analytics/heatmap");
        setData(response.data);
      } catch (error) {
        console.error("Failed to fetch analytics heatmap", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAnalytics();
  }, []);

  return (
    <div className="flex-1 p-8 md:p-12 overflow-y-auto w-full h-full bg-[#f8f9fc]">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-black text-gray-900 mb-2">Activity Calendar</h1>
        <p className="text-gray-500 mb-10 text-lg">Track your consistency and monitor the days you spoke with your AI companions.</p>

        {loading ? (
          <div className="w-full flex justify-center py-20">
            <div className="w-10 h-10 border-4 border-violet-200 border-t-violet-600 rounded-full animate-spin"></div>
          </div>
        ) : (
          <>
            <StatCards 
              totalDays={data?.total_days_active || 0}
              longestStreak={data?.longest_streak || 0}
              currentStreak={data?.current_streak || 0}
            />
            
            <ContributionHeatmap 
              data={data?.heatmap || []}
            />
          </>
        )}
      </div>
    </div>
  );
}
