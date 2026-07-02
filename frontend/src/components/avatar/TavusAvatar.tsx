"use client";

import { useEffect, useState, useCallback } from "react";
import { VideoOff } from "lucide-react";
import { tavusService } from "@/services/tavus.service";

interface Props {
  companionId: string;
}

export default function TavusAvatar({ companionId }: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [conversationUrl, setConversationUrl] = useState<string>("");

  const createConversation = useCallback(async () => {
    try {
      setLoading(true);
      const sessionData = await tavusService.createSession(companionId);
      
      if (sessionData?.conversation_url) {
        setConversationUrl(sessionData.conversation_url);
      } else {
        throw new Error("Failed to get video URL");
      }
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || "Video unavailable";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [companionId]);

  useEffect(() => {
    if (!companionId) return;
    createConversation();
  }, [createConversation]);

  if (error) {
    return (
      <div className="w-full h-[450px] rounded-2xl bg-slate-900 flex flex-col items-center justify-center text-center p-6 shadow-lg">
        <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mb-3">
          <VideoOff size={24} className="text-slate-500" />
        </div>
        <p className="text-sm text-slate-400 font-medium">Video Unavailable</p>
        <p className="text-xs text-slate-600 mt-1 max-w-[250px]">{error.includes("402") ? "Credits required" : error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="w-full h-[450px] rounded-2xl bg-slate-900 flex items-center justify-center shadow-lg">
        <p className="text-sm text-slate-400 animate-pulse">Connecting to Avatar...</p>
      </div>
    );
  }

  return (
    // Zero hacks. Just a clean 16:9 box.
    <div className="w-full aspect-video rounded-2xl overflow-hidden bg-black shadow-xl">
      <iframe
        src={conversationUrl}
        className="w-full h-full border-none"
        allow="microphone; camera; autoplay; display-capture; fullscreen"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-presentation"
        title="Tavus Avatar"
      />
    </div>
  );
}