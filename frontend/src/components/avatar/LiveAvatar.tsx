"use client";

import { useEffect, useRef, useState } from "react";
// ✅ CORRECT SDK: LiveAvatarSession
import { LiveAvatarSession } from "@heygen/liveavatar-web-sdk";
import { liveAvatarService } from "@/services/liveavatar.service";

interface LiveAvatarProps {
  lastAssistantMessage?: string;
}

export default function LiveAvatar({ lastAssistantMessage }: LiveAvatarProps) {
  const sessionRef = useRef<LiveAvatarSession | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [debugMessage, setDebugMessage] = useState("Initializing...");

  // 1. Initialize Session
  useEffect(() => {
    let isMounted = true;

    const startAvatar = async () => {
      try {
        setDebugMessage("Requesting session token...");
        const data = await liveAvatarService.createSession();
        
        if (!isMounted) return;
        if (!data?.sessionToken) throw new Error("No session token");

        setDebugMessage("Starting session...");

        // Initialize using the current SDK
        const session = new LiveAvatarSession(
          data.sessionToken,
          { videoElement: videoRef.current! } as any
        );

        sessionRef.current = session;
        await session.start();

        setDebugMessage("Session started successfully.");
        setLoading(false);
      } catch (err: any) {
        setDebugMessage(`Error: ${err.message}`);
        setLoading(false);
      }
    };

    startAvatar();

    return () => {
      isMounted = false;
      sessionRef.current?.stop();
    };
  }, []);

  // 2. Speak via Task API
  useEffect(() => {
    const speak = async () => {
      if (!lastAssistantMessage || !sessionRef.current) return;

      try {
        // Accessing session internals to trigger the task
        const session = sessionRef.current as any;
        const token = session.sessionClient?.sessionToken;
        const sessionId = session.sessionId;

        if (!token || !sessionId) return;

        await fetch("https://api.liveavatar.com/v1/sessions/task", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify({
            session_id: sessionId,
            text: lastAssistantMessage,
            task_type: "repeat",
          }),
        });
      } catch (err) {
        console.error("Speak Task Failed:", err);
      }
    };

    speak();
  }, [lastAssistantMessage]);

  return (
    <div className="w-full rounded-3xl border border-[#ECEAF4] bg-white p-4 shadow-sm">
      <div className="relative w-full h-105 rounded-2xl bg-black overflow-hidden">
        <video 
          ref={videoRef} 
          autoPlay 
          playsInline 
          muted 
          className="w-full h-full object-cover" 
        />
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/80 text-white text-sm">
            {debugMessage}
          </div>
        )}
      </div>
      <div className="mt-4 p-4 text-sm text-slate-700 bg-slate-50 rounded-2xl">
        <p>{debugMessage}</p>
      </div>
    </div>
  );
}