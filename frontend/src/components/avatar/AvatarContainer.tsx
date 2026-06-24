"use client";

import LiveAvatar from "./LiveAvatar";

interface AvatarContainerProps {
  lastAssistantMessage?: string;
}

export default function AvatarContainer({
  lastAssistantMessage,
}: AvatarContainerProps) {
  return (
    <div className="flex justify-center py-4">
      <LiveAvatar
        lastAssistantMessage={lastAssistantMessage}
      />
    </div>
  );
}