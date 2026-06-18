"use client";

import LiveAvatar from "./LiveAvatar";

interface Props {
  speaking: boolean;
}

export default function AvatarContainer({
  speaking
}: Props) {

  return (

    <div
      className="
        flex
        justify-center
        mb-6
      "
    >

      <LiveAvatar
        speaking={speaking}
      />

    </div>

  );
}