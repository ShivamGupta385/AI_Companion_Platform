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
  onSpeakEnd
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
          onSpeakStart={
            onSpeakStart
          }
          onSpeakEnd={
            onSpeakEnd
          }
        />

      ))}

    </div>

  );
}