"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Square, Volume2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";

import { ttsService } from "@/services/tts.service";

interface MessageBubbleProps {
  senderType: string;
  message: string;
  onSpeakStart?: () => void;
  onSpeakEnd?: () => void;
}

export default function MessageBubble({
  senderType,
  message,
  onSpeakStart,
  onSpeakEnd,
}: MessageBubbleProps) {
  const isUser = senderType === "user";

  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);

  const cleanupAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.onplay = null;
      audioRef.current.onended = null;
      audioRef.current.onerror = null;
      audioRef.current = null;
    }

    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }

    setIsPlayingAudio(false);
    setIsLoadingAudio(false);
    onSpeakEnd?.();
  };

  const stopAudio = () => {
    cleanupAudio();
  };

  const handleSpeak = async () => {
    if (isUser) return;

    if (isPlayingAudio || isLoadingAudio) {
      stopAudio();
      return;
    }

    try {
      setIsLoadingAudio(true);
      const blob = await ttsService.speak(message);
      const url = URL.createObjectURL(blob);
      audioUrlRef.current = url;

      const audio = new Audio(url);
      audioRef.current = audio;

      audio.onplay = () => {
        setIsLoadingAudio(false);
        setIsPlayingAudio(true);
        onSpeakStart?.();
      };

      audio.onended = () => cleanupAudio();
      audio.onerror = () => {
        console.error("Audio playback failed");
        cleanupAudio();
      };

      await audio.play();
    } catch (error) {
      console.error("TTS Error:", error);
      cleanupAudio();
    }
  };

  useEffect(() => {
    return () => cleanupAudio();
  }, []);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`
          px-5
          py-3
          shadow-sm
          overflow-hidden
          ${
            isUser
              ? "max-w-[70%] rounded-2xl rounded-br-sm bg-violet-600 text-white shadow-md text-right"
              : "max-w-[80%] rounded-2xl rounded-bl-sm bg-white text-slate-800 border border-slate-100 shadow-md text-left"
          }
        `}
      >
        {/* AI Header */}
        {!isUser && (
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-full bg-violet-100 flex items-center justify-center text-base">
              🤖
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-900">AI Companion</h4>
              <p className="text-xs text-slate-400">Online</p>
            </div>
          </div>
        )}

        {/* Message Text - Fixed overflow and spacing */}
        <div className="prose prose-sm prose-slate max-w-none [&_p]:my-1 [&_ul]:my-1 [&_ol]:my-1 [&_li]:my-0.5">
          <ReactMarkdown remarkPlugins={[remarkBreaks]}>
            {message}
          </ReactMarkdown>
        </div>

        {/* Listen Button (Only for AI) */}
        {!isUser && (
          <div className="mt-3 flex items-center">
            <button
              onClick={handleSpeak}
              disabled={isLoadingAudio}
              className={`
                flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full transition
                ${
                  isPlayingAudio
                    ? "bg-red-50 text-red-600 hover:bg-red-100"
                    : "bg-violet-50 text-violet-600 hover:bg-violet-100"
                }
                ${isLoadingAudio ? "opacity-70 cursor-not-allowed" : ""}
              `}
            >
              {isLoadingAudio ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Loading...
                </>
              ) : isPlayingAudio ? (
                <>
                  <Square size={14} />
                  Stop
                </>
              ) : (
                <>
                  <Volume2 size={14} />
                  Listen
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}