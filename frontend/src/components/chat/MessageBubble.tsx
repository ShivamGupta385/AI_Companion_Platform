interface MessageBubbleProps {
  senderType: string;
  message: string;
}

export default function MessageBubble({
  senderType,
  message,
}: MessageBubbleProps) {

  const isUser =
    senderType === "user";

  return (
    <div
      className={`flex ${
        isUser
          ? "justify-end"
          : "justify-start"
      }`}
    >
      <div
        className={`
          max-w-[70%]
          rounded-xl
          px-4
          py-3
          ${
            isUser
              ? "bg-black text-white"
              : "bg-gray-200 text-black"
          }
        `}
      >
        {message}
      </div>
    </div>
  );
}