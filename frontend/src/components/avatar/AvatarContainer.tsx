"use client";

import TavusAvatar from "./TavusAvatar";

interface AvatarContainerProps {
  companionId: string;
  companionName: string;
}

export default function AvatarContainer({
  companionId,
  companionName,
}: AvatarContainerProps) {
  return (
    <div className="flex justify-center py-4 w-full">
      <TavusAvatar
        companionId={companionId}
        companionName={companionName}
      />
    </div>
  );
}