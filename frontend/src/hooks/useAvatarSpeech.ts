"use client";

import {
  useRef,
  useState,
} from "react";

export function useAvatarSpeech() {
  const [isSpeaking, setIsSpeaking] =
    useState(false);

  const utteranceRef =
    useRef<SpeechSynthesisUtterance | null>(
      null
    );

  const speak = (
    text: string
  ) => {
    if (!text.trim()) return;

    // stop old speech if any
    window.speechSynthesis.cancel();

    const utterance =
      new SpeechSynthesisUtterance(
        text
      );

    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onstart = () => {
      setIsSpeaking(true);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
    };

    utteranceRef.current =
      utterance;

    window.speechSynthesis.speak(
      utterance
    );
  };

  const stop = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  };

  return {
    isSpeaking,
    speak,
    stop,
  };
}