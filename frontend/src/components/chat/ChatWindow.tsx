import { Message } from "@/types/chat.types";
import MessageBubble from "./MessageBubble";

interface ChatWindowProps {
  messages: Message[];
}

export default function ChatWindow({
  messages,
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
        />
      ))}
    </div>
  );
}