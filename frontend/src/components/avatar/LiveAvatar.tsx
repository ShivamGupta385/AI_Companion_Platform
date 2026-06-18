"use client";

import Image from "next/image";

interface Props {
  speaking: boolean;
}

export default function LiveAvatar({
  speaking
}: Props) {

  return (

    <div
      className="
        flex
        flex-col
        items-center
        justify-center
        py-4
      "
    >

      <div
        className="
          relative
          w-[280px]
          h-[280px]
        "
      >

        <Image
          src="/avatar/haru/runtime/haru.1024/texture_00.png"
          alt="Haru Avatar"
          fill
          className="
            object-contain
            select-none
          "
          priority
        />

      </div>

      <div
        className={`
          mt-4
          bg-black
          transition-all
          duration-100

          ${
            speaking
              ? "w-14 h-6 rounded-full"
              : "w-10 h-2 rounded-md"
          }
        `}
      />

      <p
        className="
          text-xs
          text-gray-500
          mt-2
        "
      >
        {speaking
          ? "Speaking..."
          : "Idle"}
      </p>

    </div>

  );
}