"use client";

import { useState } from "react";

interface ChatInputProps {
  onSend: (
    message: string
  ) => void;
  loading: boolean;
}

export default function ChatInput({
  onSend,
  loading,
}: ChatInputProps) {

  const [message, setMessage] =
    useState("");

  const handleSend = () => {

    if (!message.trim())
      return;

    onSend(message);

    setMessage("");
  };

  return (
    <div className="flex gap-2">

      <input
        className="flex-1 border rounded-lg px-4 py-2"
        placeholder="Type a message..."
        value={message}
        onChange={(e) =>
          setMessage(
            e.target.value
          )
        }
      />

      <button
        onClick={handleSend}
        disabled={loading}
        className="bg-black text-white px-6 py-2 rounded-lg"
      >
        Send
      </button>

    </div>
  );
}