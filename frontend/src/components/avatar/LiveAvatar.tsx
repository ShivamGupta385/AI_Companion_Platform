"use client";

import { useEffect, useRef, useState } from "react";
import { LiveAvatarSession } from "@heygen/liveavatar-web-sdk";
import { liveAvatarService } from "@/services/liveavatar.service";

interface LiveAvatarProps {
  lastAssistantMessage?: string;
}

export default function LiveAvatar({
  lastAssistantMessage,
}: LiveAvatarProps) {
  const sessionRef =
    useRef<LiveAvatarSession | null>(null);

  const videoRef =
    useRef<HTMLVideoElement | null>(null);

  const hasStartedRef =
    useRef(false);

  const isStoppingRef =
    useRef(false);

  const attachRetryRef =
    useRef<NodeJS.Timeout | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [sessionStarted, setSessionStarted] =
    useState(false);

  const [videoMounted, setVideoMounted] =
    useState(false);

  const [debugMessage, setDebugMessage] =
    useState("Initializing LiveAvatar...");

  // ------------------------------------------------------
  // Attach remote video to <video>
  // ------------------------------------------------------
  const attachRemoteVideo = (
    session: any
  ) => {
    try {
      console.log(
        "[LIVEAVATAR] Session keys:",
        Object.keys(session || {})
      );

      if (!videoRef.current) {
        console.warn(
          "[LIVEAVATAR] videoRef is not available"
        );
        return false;
      }

      const videoEl = videoRef.current;

      // --------------------------------------------------
      // 1) Preferred: LiveKit style remote video track
      // --------------------------------------------------
      const remoteVideoTrack =
        session?._remoteVideoTrack;

      if (
        remoteVideoTrack &&
        typeof remoteVideoTrack.attach === "function"
      ) {
        console.log(
          "[LIVEAVATAR] Attaching _remoteVideoTrack..."
        );

        try {
          remoteVideoTrack.attach(videoEl);

          videoEl.autoplay = true;
          videoEl.playsInline = true;
          videoEl.muted = true;

          setVideoMounted(true);
          setDebugMessage(
            "Remote video track attached successfully."
          );

          return true;
        } catch (err) {
          console.error(
            "[LIVEAVATAR] _remoteVideoTrack attach failed:",
            err
          );
        }
      }

      // --------------------------------------------------
      // 2) Fallback: direct MediaStream fields
      // --------------------------------------------------
      const mediaStream =
        session?.mediaStream ||
        session?.stream ||
        session?._mediaStream ||
        session?._remoteStream;

      if (mediaStream) {
        console.log(
          "[LIVEAVATAR] Attaching MediaStream fallback..."
        );

        try {
          videoEl.srcObject = mediaStream;
          videoEl.autoplay = true;
          videoEl.playsInline = true;
          videoEl.muted = true;

          videoEl.play().catch((err) => {
            console.error(
              "[LIVEAVATAR] video play failed:",
              err
            );
          });

          setVideoMounted(true);
          setDebugMessage(
            "Remote MediaStream attached successfully."
          );

          return true;
        } catch (err) {
          console.error(
            "[LIVEAVATAR] MediaStream attach failed:",
            err
          );
        }
      }

      // --------------------------------------------------
      // 3) Fallback: try to read track from session.room
      // --------------------------------------------------
      const room = session?.room;

      if (room?.remoteParticipants) {
        console.log(
          "[LIVEAVATAR] Trying session.room remote participants..."
        );

        try {
          for (const participant of room.remoteParticipants.values()) {
            const trackPublications =
              participant?.trackPublications;

            if (!trackPublications) continue;

            for (const publication of trackPublications.values()) {
              const track =
                publication?.videoTrack ||
                publication?.track;

              if (
                track &&
                typeof track.attach === "function"
              ) {
                console.log(
                  "[LIVEAVATAR] Attaching participant track..."
                );

                track.attach(videoEl);

                videoEl.autoplay = true;
                videoEl.playsInline = true;
                videoEl.muted = true;

                setVideoMounted(true);
                setDebugMessage(
                  "Remote participant video track attached successfully."
                );

                return true;
              }
            }
          }
        } catch (err) {
          console.error(
            "[LIVEAVATAR] session.room fallback failed:",
            err
          );
        }
      }

      console.warn(
        "[LIVEAVATAR] No renderable remote video track / stream found."
      );

      setDebugMessage(
        "Session started, but no remote video track was found yet."
      );

      return false;
    } catch (err) {
      console.error(
        "[LIVEAVATAR] attachRemoteVideo error:",
        err
      );

      setDebugMessage(
        "attachRemoteVideo crashed."
      );

      return false;
    }
  };

  // ------------------------------------------------------
  // Start session once
  // ------------------------------------------------------
  useEffect(() => {
    let mounted = true;

    const startAvatar = async () => {
      try {
        // Prevent duplicate init
        if (
          hasStartedRef.current ||
          sessionRef.current
        ) {
          console.log(
            "[LIVEAVATAR] Session already started / starting. Skipping duplicate init."
          );
          return;
        }

        hasStartedRef.current = true;

        setLoading(true);
        setError(null);
        setDebugMessage(
          "Requesting LiveAvatar session..."
        );

        const data =
          await liveAvatarService.createSession();

        console.log(
          "[LIVEAVATAR] Backend response:",
          data
        );

        if (!mounted) return;

        if (!data?.sessionToken) {
          throw new Error(
            "No LiveAvatar sessionToken returned from backend"
          );
        }

        setDebugMessage(
          "Session token received. Starting LiveAvatar session..."
        );

        const session =
          new LiveAvatarSession(
            data.sessionToken,
            {
              voiceChat: true,
            }
          );

        sessionRef.current = session;

        await session.start();

        console.log(
          "✅ LiveAvatar session started"
        );
        console.log(
          "[LIVEAVATAR] Session object:",
          session
        );

        if (!mounted) return;

        setSessionStarted(true);
        setDebugMessage(
          "Session started. Waiting for remote video track..."
        );

        // --------------------------------------------------
        // Retry attaching video for a few seconds because
        // remote track may appear after session.start()
        // --------------------------------------------------
        let attempts = 0;
        const maxAttempts = 12;

        const tryAttach = () => {
          if (
            !mounted ||
            !sessionRef.current
          ) {
            return;
          }

          attempts += 1;

          const attached =
            attachRemoteVideo(
              sessionRef.current
            );

          if (attached) {
            console.log(
              "[LIVEAVATAR] Video attached successfully."
            );

            if (attachRetryRef.current) {
              clearInterval(
                attachRetryRef.current
              );
              attachRetryRef.current = null;
            }

            return;
          }

          console.log(
            `[LIVEAVATAR] attach attempt ${attempts}/${maxAttempts} failed`
          );

          if (attempts >= maxAttempts) {
            if (attachRetryRef.current) {
              clearInterval(
                attachRetryRef.current
              );
              attachRetryRef.current = null;
            }

            setDebugMessage(
              "Session started, but avatar video was not mounted after multiple retries."
            );
          }
        };

        tryAttach();

        attachRetryRef.current =
          setInterval(() => {
            tryAttach();
          }, 1000);
      } catch (err: any) {
        console.error(
          "❌ LiveAvatar start failed:",
          err
        );

        hasStartedRef.current = false;

        const message =
          err?.message ||
          "Failed to start LiveAvatar";

        if (
          message
            .toLowerCase()
            .includes("concurrency limit")
        ) {
          setError(
            "LiveAvatar session concurrency limit reached. Wait 20-30 seconds and refresh, or ensure previous session is fully closed."
          );
        } else {
          setError(message);
        }

        setDebugMessage(
          "LiveAvatar session failed to start."
        );
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    startAvatar();

    return () => {
      mounted = false;

      if (attachRetryRef.current) {
        clearInterval(
          attachRetryRef.current
        );
        attachRetryRef.current = null;
      }

      if (
        sessionRef.current &&
        !isStoppingRef.current
      ) {
        isStoppingRef.current = true;

        sessionRef.current
          .stop()
          .then(() => {
            console.log(
              "🛑 LiveAvatar session stopped"
            );
          })
          .catch((err) => {
            console.warn(
              "[LIVEAVATAR] stop failed / session already gone:",
              err
            );
          })
          .finally(() => {
            sessionRef.current = null;
            hasStartedRef.current = false;
            isStoppingRef.current = false;
          });
      }
    };
  }, []);

  // ------------------------------------------------------
  // Future lip-sync / speech hook
  // ------------------------------------------------------
  useEffect(() => {
    if (
      sessionStarted &&
      lastAssistantMessage
    ) {
      console.log(
        "[LIVEAVATAR] Latest AGIX response:",
        lastAssistantMessage
      );

      // FUTURE:
      // if LiveAvatar SDK supports speech injection,
      // trigger it here for lip sync.
    }
  }, [lastAssistantMessage, sessionStarted]);

  return (
    <div className="w-full rounded-3xl border border-[#ECEAF4] bg-white p-4 shadow-sm">
      <div
        className="
          relative
          w-full
          h-[420px]
          rounded-2xl
          bg-black
          overflow-hidden
        "
      >
        {/* actual avatar video */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />

        {/* loading */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/80">
            <p className="text-white text-sm">
              Starting LiveAvatar...
            </p>
          </div>
        )}

        {/* error */}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-black px-6">
            <div className="text-center">
              <p className="text-red-400 font-medium">
                LiveAvatar failed
              </p>

              <p className="text-slate-300 text-sm mt-2 whitespace-pre-wrap">
                {error}
              </p>
            </div>
          </div>
        )}

        {/* waiting for video */}
        {!loading && !error && !videoMounted && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/70 px-6">
            <div className="text-center text-white">
              <p className="font-medium">
                LiveAvatar session started
              </p>

              <p className="text-xs text-slate-300 mt-2">
                Waiting for avatar video track...
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Debug Panel */}
      <div className="mt-4 rounded-2xl bg-slate-50 border border-slate-200 p-4 text-sm text-slate-700">
        <p className="font-semibold mb-2">
          LiveAvatar Debug
        </p>

        <p>
          Session started:{" "}
          {sessionStarted ? "Yes" : "No"}
        </p>

        <p>
          Video mounted:{" "}
          {videoMounted ? "Yes" : "No"}
        </p>

        <p className="mt-2 text-slate-600 whitespace-pre-wrap">
          {debugMessage}
        </p>
      </div>
    </div>
  );
}