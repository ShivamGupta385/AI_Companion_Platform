"use client";

interface MessageBubbleProps {
  senderType: string;
  message: string;
}

export default function MessageBubble({
  senderType,
  message,
}: MessageBubbleProps) {
  const isUser = senderType === "user";

  return (
    <div
      className={`flex ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`
          max-w-[75%]
          rounded-[28px]
          px-5
          py-4
          shadow-sm
          border
          ${
            isUser
              ? `
                bg-gradient-to-r
                from-violet-500
                to-purple-600
                text-white
                border-transparent
              `
              : `
                bg-white
                text-slate-800
                border-[#ECEAF4]
              `
          }
        `}
      >
        {!isUser && (
          <div className="flex items-center gap-3 mb-3">
            <div
              className="
                w-10
                h-10
                rounded-full
                bg-violet-100
                flex
                items-center
                justify-center
                text-lg
              "
            >
              🤖
            </div>

            <div>
              <h4
                className="
                  text-sm
                  font-semibold
                  text-slate-900
                "
              >
                AI Companion
              </h4>

              <p
                className="
                  text-xs
                  text-slate-500
                "
              >
                Online
              </p>
            </div>
          </div>
        )}

        <p
          className="
            whitespace-pre-wrap
            leading-7
          "
        >
          {message}
        </p>
      </div>
    </div>
  );
}
