"use client";

import {
  useEffect,
  useRef
} from "react";

import {
  LiveAvatarSession
} from "@heygen/liveavatar-web-sdk";

import {
  liveAvatarService
} from "@/services/liveavatar.service";

export default function LiveAvatar() {

  const sessionRef =
    useRef<LiveAvatarSession | null>(
      null
    );
  
  const avatarContainerRef =
  useRef<HTMLDivElement>(null);

  useEffect(() => {

    let mounted = true;

    const startAvatar =
      async () => {

        try {

          if (
            sessionRef.current
          ) {

            console.log(
              "⚠️ Avatar session already running"
            );

            return;
          }

          const data =
            await liveAvatarService
              .createSession();

          if (!mounted) {
            return;
          }

          const session =
            new LiveAvatarSession(
              data.sessionToken,
              {
                voiceChat: true
              }
            );

          sessionRef.current =
            session;

          await session.start();

          console.log(
            "✅ Avatar Started"
          );

          console.log(
            "SESSION OBJECT:",
            session
          );

          console.log(
            "SESSION KEYS:",
            Object.keys(session)
          );

        } catch (error) {

          console.error(
            "❌ Session start failed:",
            error
          );

        }

      };

    startAvatar();

    return () => {

      mounted = false;

      if (
        sessionRef.current
      ) {

        sessionRef.current
          .stop()
          .then(() => {

            console.log(
              "🛑 Avatar Session Stopped"
            );

          })
          .catch(
            console.error
          );

        sessionRef.current =
          null;

      }

    };

  }, []);

  return (

    <div
      ref={avatarContainerRef}
      className="
        w-full
        h-[500px]
        border
        rounded-xl
        bg-black
      "
    />

  );

}