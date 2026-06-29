"use client";

import { useEffect, useState, useCallback } from "react";
import { tavusService } from "@/services/tavus.service";

interface Props {
  companionId: string;
  latestMessage?: string; // passed down from chat page
}

interface TavusSession {
  conversation_id: string;
  conversation_url?: string;
  replica_id?: string;
  persona_id?: string;
}

interface ChatResponse {
  response: string;
  tavus_video_url?: string;
}

export default function TavusAvatar({ companionId, latestMessage }: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [session, setSession] = useState<TavusSession | null>(null);
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null);

  // Create Tavus conversation session
  const createConversation = useCallback(async () => {
    try {
      setLoading(true);
      const sessionData: TavusSession = await tavusService.createSession(companionId);
      setSession(sessionData);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Failed to create Tavus session");
    } finally {
      setLoading(false);
    }
  }, [companionId]);

  useEffect(() => {
    if (!companionId) return;
    createConversation();
  }, [createConversation]);

  // Whenever a new message comes in from chat page, send it to Tavus
  useEffect(() => {
    const sendToTavus = async () => {
      if (!session?.conversation_id || !latestMessage) return;
      try {
        const data: ChatResponse = await tavusService.sendMessage(
          session.conversation_id,
          latestMessage
        );
        setChatResponse(data);
      } catch (err: any) {
        const detail = err?.response?.data?.detail;
        setError(typeof detail === "string" ? detail : "Failed to send message to Tavus");
      }
    };

    sendToTavus();
  }, [latestMessage, session?.conversation_id]);

  if (loading) {
    return (
      <div className="flex h-[430px] items-center justify-center rounded-3xl border bg-white shadow-sm">
        Starting Tavus Avatar...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-[430px] items-center justify-center rounded-3xl border bg-red-50 text-red-600 shadow-sm">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-6 shadow-sm">
        <h2 className="text-xl font-semibold mb-4">Tavus Avatar</h2>
        {chatResponse ? (
          <>
            <p><strong>AI Response:</strong> {chatResponse.response}</p>
            {chatResponse.tavus_video_url ? (
              <video
                src={chatResponse.tavus_video_url}
                controls
                autoPlay
                className="rounded shadow-md w-full"
              />
            ) : (
              <p className="text-slate-500">No Tavus video available.</p>
            )}
          </>
        ) : (
          <p className="text-slate-500">Waiting for AI response…</p>
        )}
      </div>
    </div>
  );
}
