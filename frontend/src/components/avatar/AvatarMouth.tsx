interface Props {
  speaking: boolean;
}

export default function AvatarMouth({
  speaking
}: Props) {

  return (

    <div
      className={`
        bg-black
        mt-2
        transition-all
        duration-150

        ${
          speaking
            ? `
              w-8
              h-4
              rounded-full
              animate-pulse
            `
            : `
              w-6
              h-1
              rounded
            `
        }
      `}
    />

  );
}