import { Message } from "@/types/chat.types";

import MessageBubble from "./MessageBubble";

interface ChatWindowProps {
  messages: Message[];
}

export default function ChatWindow({
  messages,
}: ChatWindowProps) {

  return (
    <div className="space-y-4">

      {messages.map((msg) => (
        <MessageBubble
          key={msg.id}
          senderType={
            msg.sender_type
          }
          message={
            msg.message_text
          }
        />
      ))}

    </div>
  );
}