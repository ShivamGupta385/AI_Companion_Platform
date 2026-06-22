import { Message } from "@/types/chat.types";
import MessageBubble from "./MessageBubble";

interface ChatWindowProps {
  messages: Message[];
  onSpeakStart?: () => void;
  onSpeakEnd?: () => void;
}

export default function ChatWindow({
  messages,
  onSpeakStart,
  onSpeakEnd,
}: ChatWindowProps) {
  return (
    <div
      className="
        max-w-4xl
        mx-auto
        w-full
        space-y-6
        py-6
      "
    >
      {messages.map((msg) => (
        <MessageBubble
          key={msg.id}
          senderType={msg.sender_type}
          message={msg.message_text}
          onSpeakStart={onSpeakStart}
          onSpeakEnd={onSpeakEnd}
        />
      ))}
    </div>
  );
}