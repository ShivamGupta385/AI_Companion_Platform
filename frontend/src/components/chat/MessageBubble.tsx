import { ttsService } from "@/services/tts.service";

interface MessageBubbleProps {
  senderType: string;
  message: string;
  onSpeakStart?: () => void;
  onSpeakEnd?: () => void;
}

export default function MessageBubble({
  senderType,
  message,
  onSpeakStart,
  onSpeakEnd
}: MessageBubbleProps) {

  const isUser =
    senderType === "user";

  const handleSpeak =
    async () => {

      try {

        const blob =
          await ttsService.speak(
            message
          );

        const url =
          URL.createObjectURL(
            blob
          );

        const audio =
          new Audio(url);

        audio.onplay = () => {

          onSpeakStart?.();

        };

        audio.onended = () => {

          onSpeakEnd?.();

        };

        await audio.play();
      } catch (error) {

        console.error(
          "TTS Error:",
          error
        );
      }
    };

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

        <p>
          {message}
        </p>

        {!isUser && (

          <button
            onClick={handleSpeak}
            className="
              mt-2
              text-sm
              text-blue-600
              hover:text-blue-800
            "
          >
            🔊 Listen
          </button>

        )}

      </div>

    </div>
  );
}