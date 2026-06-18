import AvatarMouth from "./AvatarMouth";

interface AvatarProps {
  speaking: boolean;
}

export default function Avatar({
  speaking
}: AvatarProps) {

  return (

    <div className="flex flex-col items-center">

      <div className="text-8xl">
        🤖
      </div>

      <AvatarMouth
        speaking={speaking}
      />

    </div>

  );
}