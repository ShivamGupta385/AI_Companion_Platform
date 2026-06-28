"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  Loader2,
  Square,
  Volume2,
} from "lucide-react";

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

    // If same bubble is already speaking,
    // clicking again should stop it.
    if (isPlayingAudio || isLoadingAudio) {
      stopAudio();
      return;
    }

    try {
      setIsLoadingAudio(true);

      const blob = await ttsService.speak(message);

      // 👇 ADDED: Safety check for null blob (LiveAvatar handles audio) 👇
      if (!blob) {
        console.log("No audio blob returned (Avatar is handling speech).");
        setIsLoadingAudio(false);
        return;
      }

      const url = URL.createObjectURL(blob);

      audioUrlRef.current = url;

      const audio = new Audio(url);

      audioRef.current = audio;

      audio.onplay = () => {
        setIsLoadingAudio(false);
        setIsPlayingAudio(true);
        onSpeakStart?.();
      };

      audio.onended = () => {
        cleanupAudio();
      };

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
    return () => {
      cleanupAudio();
    };
  }, []);

  return (
    <div
      className={`flex ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`
          max-w-[75%]
          rounded-[28px]
          px-5
          py-4
          shadow-sm
          border
          ${
            isUser
              ? `
                bg-gradient-to-r
                from-violet-500
                to-purple-600
                text-white
                border-transparent
              `
              : `
                bg-white
                text-slate-800
                border-[#ECEAF4]
              `
          }
        `}
      >
        {!isUser && (
          <div className="flex items-center gap-3 mb-3">
            <div
              className="
                w-10
                h-10
                rounded-full
                bg-violet-100
                flex
                items-center
                justify-center
                text-lg
              "
            >
              🤖
            </div>

            <div>
              <h4
                className="
                  text-sm
                  font-semibold
                  text-slate-900
                "
              >
                AI Companion
              </h4>

              <p
                className="
                  text-xs
                  text-slate-500
                "
              >
                Online
              </p>
            </div>
          </div>
        )}

        <p
          className="
            whitespace-pre-wrap
            leading-7
          "
        >
          {message}
        </p>

        {!isUser && (
          <div className="mt-4 flex items-center">
            <button
              onClick={handleSpeak}
              disabled={isLoadingAudio}
              className={`
                flex
                items-center
                gap-2
                text-sm
                font-medium
                transition
                ${
                  isPlayingAudio
                    ? "text-red-600 hover:text-red-700"
                    : "text-violet-600 hover:text-violet-700"
                }
                ${
                  isLoadingAudio
                    ? "opacity-70 cursor-not-allowed"
                    : ""
                }
              `}
            >
              {isLoadingAudio ? (
                <>
                  <Loader2
                    size={16}
                    className="animate-spin"
                  />
                  Loading...
                </>
              ) : isPlayingAudio ? (
                <>
                  <Square size={16} />
                  Stop
                </>
              ) : (
                <>
                  <Volume2 size={16} />
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