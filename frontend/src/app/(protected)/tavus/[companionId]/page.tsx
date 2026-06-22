"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { tavusService } from "@/services/tavus.service";

interface TavusSessionResponse {
  conversation_id: string;
  conversation_url?: string;
  replica_id?: string;
  persona_id?: string;
}

export default function TavusAvatarPage() {
  const params = useParams();
  const companionId = params?.companionId as string;

  const [loading, setLoading] = useState(true);
  const [session, setSession] =
    useState<TavusSessionResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!companionId) return;

    const startSession = async () => {
      try {
        setLoading(true);
        const data = await tavusService.createSession(
          companionId
        );
        setSession(data);
      } catch (err: any) {
        setError(
          err?.response?.data?.detail ||
            "Failed to create Tavus session"
        );
      } finally {
        setLoading(false);
      }
    };

    startSession();
  }, [companionId]);

  return (
    <div className="min-h-screen bg-[#F8F7FF] p-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-900 mb-6">
          Tavus Avatar Session
        </h1>

        {loading && (
          <div className="bg-white rounded-3xl p-8 shadow-sm">
            Starting Tavus avatar session...
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-600 rounded-3xl p-6 shadow-sm">
            {error}
          </div>
        )}

        {!loading && session && (
          <div className="space-y-6">
            <div className="bg-white rounded-3xl p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-4">
                Tavus Session Created
              </h2>

              <p className="text-slate-600 mb-2">
                <strong>Conversation ID:</strong>{" "}
                {session.conversation_id}
              </p>

              <p className="text-slate-600 mb-2">
                <strong>Replica ID:</strong>{" "}
                {session.replica_id || "N/A"}
              </p>

              <p className="text-slate-600">
                <strong>Persona ID:</strong>{" "}
                {session.persona_id || "N/A"}
              </p>
            </div>

            <div className="bg-white rounded-3xl p-6 shadow-sm">
              <h2 className="text-xl font-semibold mb-4">
                Tavus Conversation URL
              </h2>

              {session.conversation_url ? (
                <a
                  href={session.conversation_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-violet-600 underline"
                >
                  Open Tavus Avatar Session
                </a>
              ) : (
                <p className="text-slate-500">
                  No conversation URL returned by Tavus.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}