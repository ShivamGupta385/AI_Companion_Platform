"use client";

import { useEffect, useState } from "react";
import { tavusService } from "@/services/tavus.service";

interface Props {
  companionId: string;
}

export default function TavusAvatar({
  companionId,
}: Props) {

  const [conversationUrl, setConversationUrl] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {

    const startConversation = async () => {

      try {

        const session =
          await tavusService.createSession(
            companionId
          );

        console.log(session);

        setConversationUrl(
          session.conversation_url
        );

      } catch (err) {

        console.error(err);

      } finally {

        setLoading(false);

      }

    };

    startConversation();

  }, [companionId]);

  if (loading) {

    return (
      <div className="flex h-162.5 items-center justify-center rounded-3xl bg-white">
        Creating Tavus Conversation...
      </div>
    );

  }

  if (!conversationUrl) {

    return (
      <div className="flex h-162.5 items-center justify-center rounded-3xl bg-white">
        Failed to create conversation.
      </div>
    );

  }

  return (

    <iframe
      src={conversationUrl}
      className="h-162.5 w-full rounded-3xl border-0"
      allow="camera; microphone; autoplay;"
    />

  );

}