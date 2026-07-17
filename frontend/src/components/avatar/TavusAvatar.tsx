"use client";

import { useEffect, useRef, useState } from "react";
import { tavusService } from "@/services/tavus.service";
import DailyIframe, { DailyCall } from "@daily-co/daily-js";
import { Mic, MicOff, Video, VideoOff, PhoneOff, Maximize, Minimize, Signal, Activity, Sparkles, CheckCircle2 } from "lucide-react";

interface Props {
  companionId: string;
  companionName: string;
}

interface DailyListeners {
  activeSpeakerHandler: (event: any) => void;
  participantUpdatedHandler: (event: any) => void;
  appMessageHandler: (event: any) => void;
  cameraErrorHandler: (event: any) => void;
}

declare global {
  interface Window {
    __tavusDailyCall?: DailyCall | null;
  }
}

let sharedDailyCall: DailyCall | null = null;
let sharedDailyListeners: DailyListeners | null = null;
let listenersBoundToCall: DailyCall | null = null;

const isDestroyedDailyCall = (call: DailyCall | null | undefined) => {
  if (!call) {
    return true;
  }
  const maybeDestroyed = call as DailyCall & { destroyed?: boolean; isDestroyed?: boolean };
  return Boolean(maybeDestroyed.destroyed || maybeDestroyed.isDestroyed);
};

let creatingDailyCallPromise: Promise<DailyCall> | null = null;

const getOrCreateDailyCall = async (): Promise<DailyCall> => {
  if (typeof window !== "undefined" && window.__tavusDailyCall && !isDestroyedDailyCall(window.__tavusDailyCall)) {
    sharedDailyCall = window.__tavusDailyCall;
    return sharedDailyCall;
  }

  if (sharedDailyCall && !isDestroyedDailyCall(sharedDailyCall)) {
    if (typeof window !== "undefined") {
      window.__tavusDailyCall = sharedDailyCall;
    }
    return sharedDailyCall;
  }

  if (creatingDailyCallPromise) {
    return creatingDailyCallPromise;
  }

  creatingDailyCallPromise = (async (): Promise<DailyCall> => {
    try {
      sharedDailyCall = DailyIframe.createCallObject({
        audioSource: true,
        videoSource: true,
        strictMode: true,
      });
    } catch (err) {
      console.warn("[TavusAvatar] Duplicate Daily instance detected, recovering:", err);
      const stale = DailyIframe.getCallInstance();
      if (stale) {
        try {
          await stale.destroy();
        } catch (_) {
          // best effort
        }
      }
      sharedDailyCall = DailyIframe.createCallObject({
        audioSource: true,
        videoSource: true,
        strictMode: true,
      });
    }

    if (typeof window !== "undefined") {
      window.__tavusDailyCall = sharedDailyCall;
    }

    return sharedDailyCall as DailyCall;
  })();

  try {
    return await creatingDailyCallPromise;
  } finally {
    creatingDailyCallPromise = null;
  }
};

export default function TavusAvatar({
  companionId,
  companionName,
}: Props) {
  const [callObject, setCallObject] = useState<DailyCall | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionActive, setSessionActive] = useState(false);

  const [isMicOn, setIsMicOn] = useState(true);
  const [isCameraOn, setIsCameraOn] = useState(true);

  const [callDuration, setCallDuration] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [agentState, setAgentState] = useState<"listening" | "speaking" | "thinking">("listening");
  const [canvasData, setCanvasData] = useState<{ type: string; data: any; tool_call_id?: string } | null>(null);
  const [canvasVisible, setCanvasVisible] = useState(false);
  const [momentumDone, setMomentumDone] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const controlsTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const callObjectRef = useRef<DailyCall | null>(null);
  const dailyListenersRef = useRef<DailyListeners | null>(null);
  const currentConversationIdRef = useRef("");
  const sessionActiveRef = useRef(false);
  const joinInProgressRef = useRef(false);

  useEffect(() => {
    currentConversationIdRef.current = currentConversationId;
  }, [currentConversationId]);

  useEffect(() => {
    sessionActiveRef.current = sessionActive;
  }, [sessionActive]);

  const registerDailyListeners = (call: DailyCall) => {
    const activeSpeakerHandler = (event: any) => {
      if (event.activeSpeaker?.peerId === call.participants().local?.session_id) {
        setAgentState("listening");
      } else {
        setAgentState("speaking");
      }
    };

    const participantUpdatedHandler = (event: any) => {
      const participant = event.participant;

      if (
        participant.local &&
        participant.tracks.video?.state === "playable" &&
        participant.tracks.video.persistentTrack &&
        localVideoRef.current
      ) {
        const stream = localVideoRef.current.srcObject as MediaStream;
        if (!stream || !stream.getTracks().includes(participant.tracks.video.persistentTrack)) {
          localVideoRef.current.srcObject = new MediaStream([participant.tracks.video.persistentTrack]);
        }
      }

      if (!participant.local) {
        if (
          participant.tracks.video?.state === "playable" &&
          participant.tracks.video.persistentTrack &&
          videoRef.current
        ) {
          const stream = videoRef.current.srcObject as MediaStream;
          if (!stream || !stream.getTracks().includes(participant.tracks.video.persistentTrack)) {
            videoRef.current.srcObject = new MediaStream([participant.tracks.video.persistentTrack]);
          }
        }

        if (
          participant.tracks.audio?.state === "playable" &&
          participant.tracks.audio.persistentTrack &&
          audioRef.current
        ) {
          const stream = audioRef.current.srcObject as MediaStream;
          if (!stream || !stream.getTracks().includes(participant.tracks.audio.persistentTrack)) {
            audioRef.current.srcObject = new MediaStream([participant.tracks.audio.persistentTrack]);
            audioRef.current.play().catch((err) => {
              console.error("[TavusAvatar] Remote audio play() failed:", err);
            });
          }
        }
      }
    };

    const appMessageHandler = (event: any) => {
      try {
        const payload = typeof event.data === "string" ? JSON.parse(event.data) : event.data;

        const findCanvasToolCall = (value: any, depth = 0): { name: string; args: any; id?: string } | null => {
          if (depth > 10) return null;

          if (typeof value === "string") {
            const trimmed = value.trim();
            if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
              try {
                return findCanvasToolCall(JSON.parse(trimmed), depth + 1);
              } catch {
                return null;
              }
            }
            return null;
          }

          if (!value || typeof value !== "object") return null;

          const name = value.tool_name || value.name || value.function?.name;
          if (typeof name === "string" && name.startsWith("canvas_show_")) {
            const argsStr = value.arguments || value.function?.arguments;
            const args = typeof argsStr === "string" ? JSON.parse(argsStr) : (argsStr || {});
            return { name, args, id: value.tool_call_id || value.id };
          }

          if (value.component && typeof value.component === "string" && value.component.startsWith("canvas.")) {
            const mappedName = value.component.replace("canvas.", "canvas_show_");
            return { name: mappedName, args: value.data || value.value || value, id: value.tool_call_id || value.interaction_id || value.id };
          }

          if (name === "magic_canvas" && value.arguments) {
            const argsStr = value.arguments;
            const args = typeof argsStr === "string" ? JSON.parse(argsStr) : argsStr;
            if (args.component) {
              const mappedName = args.component.startsWith("canvas.") ? args.component.replace("canvas.", "canvas_show_") : `canvas_show_${args.component}`;
              return { name: mappedName, args: args.data || args, id: value.tool_call_id || value.id };
            }
          }

          if (Array.isArray(value)) {
            for (const item of value) {
              const result = findCanvasToolCall(item, depth + 1);
              if (result) return result;
            }
          } else {
            for (const key in value) {
              const result = findCanvasToolCall(value[key], depth + 1);
              if (result) return result;
            }
          }

          return null;
        };

        const toolCall = findCanvasToolCall(payload);
        if (toolCall) {
          setCanvasData({ type: toolCall.name, data: toolCall.args, tool_call_id: toolCall.id });
          setCanvasVisible(true);
          setMomentumDone(false);
        }
      } catch (error) {
        console.error("Error parsing app-message", error);
      }
    };

    const cameraErrorHandler = (event: any) => {
      console.error("Camera Error: Your webcam is currently in use by another application or blocked.", event);
      alert("Camera Error: Could not access your webcam. It might be in use by another app (like Zoom or OBS). Please close other video apps and try again.");
    };

    call.on("active-speaker-change", activeSpeakerHandler);
    call.on("participant-updated", participantUpdatedHandler);
    call.on("app-message", appMessageHandler);
    call.on("camera-error", cameraErrorHandler);

    const listeners = {
      activeSpeakerHandler,
      participantUpdatedHandler,
      appMessageHandler,
      cameraErrorHandler,
    };

    dailyListenersRef.current = listeners;
    return listeners;
  };

  const ensureListenersAttached = (call: DailyCall) => {
    if (listenersBoundToCall === call && sharedDailyListeners) {
      return;
    }

    if (listenersBoundToCall && sharedDailyListeners) {
      try {
        listenersBoundToCall.off("active-speaker-change", sharedDailyListeners.activeSpeakerHandler);
        listenersBoundToCall.off("participant-updated", sharedDailyListeners.participantUpdatedHandler);
        listenersBoundToCall.off("app-message", sharedDailyListeners.appMessageHandler);
        listenersBoundToCall.off("camera-error", sharedDailyListeners.cameraErrorHandler);
      } catch (_) {
        // old instance may already be destroyed -- best effort
      }
    }

    sharedDailyListeners = registerDailyListeners(call);
    listenersBoundToCall = call;
  };

  const ensureDailyCall = async () => {
    const call = await getOrCreateDailyCall();
    callObjectRef.current = call;
    setCallObject(call);

    ensureListenersAttached(call);

    return call;
  };

  useEffect(() => {
    const existing =
      typeof window !== "undefined" && window.__tavusDailyCall && !isDestroyedDailyCall(window.__tavusDailyCall)
        ? window.__tavusDailyCall
        : sharedDailyCall && !isDestroyedDailyCall(sharedDailyCall)
        ? sharedDailyCall
        : null;

    if (existing) {
      callObjectRef.current = existing;
      setCallObject(existing);
      ensureListenersAttached(existing);
    }

    return () => {
      if (sharedDailyListeners && listenersBoundToCall) {
        listenersBoundToCall.off("active-speaker-change", sharedDailyListeners.activeSpeakerHandler);
        listenersBoundToCall.off("participant-updated", sharedDailyListeners.participantUpdatedHandler);
        listenersBoundToCall.off("app-message", sharedDailyListeners.appMessageHandler);
        listenersBoundToCall.off("camera-error", sharedDailyListeners.cameraErrorHandler);
      }
    };
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (sessionActive) {
      interval = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    } else {
      setCallDuration(0);
    }
    return () => clearInterval(interval);
  }, [sessionActive]);

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  const handleMouseMove = () => {
    setShowControls(true);
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    controlsTimeoutRef.current = setTimeout(() => {
      setShowControls(false);
    }, 3000);
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen().catch(console.error);
    } else {
      document.exitFullscreen().catch(console.error);
    }
  };

  const handleStartConversation = async () => {
    if (loading || sessionActive || joinInProgressRef.current) {
      return;
    }

    joinInProgressRef.current = true;
    setLoading(true);

    try {
      const session = await tavusService.createSession(companionId);
      setCurrentConversationId(session.conversation_id);

      const call = await ensureDailyCall();

      if (!call) {
        throw new Error("Daily call object is not ready.");
      }

      try {
        await call.join({ url: session.conversation_url });
      } catch (error: any) {
        if (error?.message?.includes("Use after destroy") || error?.message?.includes("destroyed")) {
          console.warn("Daily call was destroyed. Recreating and retrying join.", error);
          const recreatedCall = await getOrCreateDailyCall();
          callObjectRef.current = recreatedCall;
          setCallObject(recreatedCall);
          ensureListenersAttached(recreatedCall);
          await recreatedCall.join({ url: session.conversation_url });
        } else {
          throw error;
        }
      }
      setSessionActive(true);
      setShowControls(true);
    } catch (error) {
      console.error("Failed to start Daily conversation", error);
      setSessionActive(false);
    } finally {
      setLoading(false);
      joinInProgressRef.current = false;
    }
  };

  useEffect(() => {
    const currentCall = callObjectRef.current;
    if (sessionActive && currentCall) {
      const participants = currentCall.participants();

      if (participants.local?.tracks.video?.persistentTrack && localVideoRef.current) {
        const stream = localVideoRef.current.srcObject as MediaStream;
        if (!stream || !stream.getTracks().includes(participants.local.tracks.video.persistentTrack)) {
          localVideoRef.current.srcObject = new MediaStream([participants.local.tracks.video.persistentTrack]);
        }
      }

      for (const participant of Object.values(participants)) {
        if (participant.local) continue;

        if (participant.tracks.video?.persistentTrack && videoRef.current) {
          const stream = videoRef.current.srcObject as MediaStream;
          if (!stream || !stream.getTracks().includes(participant.tracks.video.persistentTrack)) {
            videoRef.current.srcObject = new MediaStream([participant.tracks.video.persistentTrack]);
          }
        }

        if (participant.tracks.audio?.persistentTrack && audioRef.current) {
          const stream = audioRef.current.srcObject as MediaStream;
          if (!stream || !stream.getTracks().includes(participant.tracks.audio.persistentTrack)) {
            audioRef.current.srcObject = new MediaStream([participant.tracks.audio.persistentTrack]);
            audioRef.current.play().catch((err) => {
              console.error("[TavusAvatar] Remote audio play() failed (fallback binder):", err);
            });
          }
        }
      }
    }
  }, [sessionActive]);

  const handleEndConversation = async () => {
    if (!currentConversationIdRef.current || loading) {
      return;
    }

    setLoading(true);

    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen().catch(console.error);
      }

      try {
        await tavusService.endSession(currentConversationIdRef.current);
      } catch (backendError) {
        console.warn("Backend end session failed or already ended:", backendError);
      }

      setSessionActive(false);
      setCurrentConversationId("");
      setIsMicOn(true);
      setIsCameraOn(true);
      setAgentState("listening");
      setCanvasData(null);
      setCanvasVisible(false);

      const currentCall = callObjectRef.current ?? sharedDailyCall;
      if (currentCall) {
        try {
          await currentCall.leave();
        } catch (error) {
          console.warn("Leave failed:", error);
        }
        try {
          await currentCall.destroy();
        } catch (error) {
          console.warn("Destroy failed:", error);
        }
      }

      sharedDailyCall = null;
      sharedDailyListeners = null;
      listenersBoundToCall = null;
      if (typeof window !== "undefined") {
        window.__tavusDailyCall = null;
      }

      callObjectRef.current = null;
      setCallObject(null);
      dailyListenersRef.current = null;

      if (videoRef.current) videoRef.current.srcObject = null;
      if (audioRef.current) audioRef.current.srcObject = null;
      if (localVideoRef.current) localVideoRef.current.srcObject = null;
    } catch (error) {
      console.error("Critical error in handleEndConversation:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleMic = () => {
    const currentCall = callObjectRef.current;
    if (currentCall) {
      const newState = !isMicOn;
      currentCall.setLocalAudio(newState);
      setIsMicOn(newState);
    }
  };

  const toggleCamera = () => {
    const currentCall = callObjectRef.current;
    if (currentCall) {
      const newState = !isCameraOn;
      currentCall.setLocalVideo(newState);
      setIsCameraOn(newState);
    }
  };

  const submitCanvasResult = (result: any) => {
    const currentCall = callObjectRef.current;
    if (currentCall && canvasData?.tool_call_id) {
      currentCall.sendAppMessage({
        message_type: "conversation",
        event_type: "conversation.tool_result",
        tool_call_id: canvasData.tool_call_id,
        result,
      });
    }
    setCanvasVisible(false);
  };

  useEffect(() => {
    return () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className={`flex flex-col w-full rounded-3xl bg-white overflow-hidden shadow-sm relative ${sessionActive ? "h-full" : "h-162.5"}`}>
      {!sessionActive ? (
        <div className="flex flex-col flex-1 items-center justify-center p-6 text-center">
          <h3>Ready to chat with {companionName}?</h3>
          <p className="text-gray-500 mb-8 max-w-md">
            Click the button below to start a video conversation with your AI companion.
          </p>
          <button
            onClick={handleStartConversation}
            disabled={loading}
            className="px-8 py-4 bg-primary text-white rounded-full font-semibold text-lg shadow-lg hover:bg-primary/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Connecting..." : "Start Conversation"}
          </button>
        </div>
      ) : (
        <div
          ref={containerRef}
          className="relative h-full w-full bg-black flex flex-col group min-h-162.5"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setShowControls(false)}
        >
          <div className={`absolute top-0 left-0 w-full p-6 flex justify-between items-start z-20 transition-opacity duration-500 ${showControls ? "opacity-100" : "opacity-0"}`}>
            <div className="flex flex-col gap-3">
              <div className="flex gap-3">
                <div className="flex items-center gap-2 bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-full text-white text-sm font-medium">
                  <Signal size={16} className="text-green-400" />
                  <span>HD</span>
                </div>
                <div className="flex items-center gap-2 bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-full text-white text-sm font-medium font-mono">
                  {formatDuration(callDuration)}
                </div>
              </div>

              <div className="flex items-center gap-2 bg-black/40 backdrop-blur-md px-4 py-2 rounded-full text-white text-sm font-medium shadow-lg transition-all duration-300 w-max">
                <Activity size={16} className={agentState === "speaking" ? "text-green-400 animate-pulse" : "text-gray-400"} />
                <span>
                  {agentState === "speaking"
                    ? `${companionName} is speaking...`
                    : `${companionName} is listening...`}
                </span>
              </div>
            </div>

            <button onClick={toggleFullscreen} className="bg-black/40 backdrop-blur-md p-3 rounded-full text-white hover:bg-black/60 transition">
              {isFullscreen ? <Minimize size={20} /> : <Maximize size={20} />}
            </button>
          </div>

          <video
            ref={videoRef}
            autoPlay
            playsInline
            className={`w-full h-full object-cover transition-all duration-300 ${agentState === "speaking" ? "ring-2 ring-primary/30" : ""}`}
          />
          <audio ref={audioRef} autoPlay />

            {canvasVisible && canvasData && (
            <div className="absolute inset-0 flex items-center justify-center p-8 z-30 pointer-events-none">
              <div className="relative bg-white/95 backdrop-blur-xl p-8 rounded-3xl shadow-2xl max-w-2xl w-full border border-gray-200 pointer-events-auto transform transition-all duration-500 scale-100 opacity-100">
                <button
                  onClick={() => setCanvasVisible(false)}
                  className="absolute top-4 right-4 text-gray-500 hover:text-gray-800 p-2 z-50"
                >
                  ✕
                </button>

                {canvasData.type === "canvas_show_momentum_map" && (
                  <div>
                    <style>{`
                      @keyframes momentumSpark {
                        0% { left: -10%; opacity: 0; }
                        15% { opacity: 1; }
                        85% { opacity: 1; }
                        100% { left: 110%; opacity: 0; }
                      }
                      @keyframes momentumGlow {
                        0%, 100% { box-shadow: 0 0 0 0 rgba(var(--momentum-glow, 217 119 87), 0.35); }
                        50% { box-shadow: 0 0 0 10px rgba(var(--momentum-glow, 217 119 87), 0); }
                      }
                    `}</style>

                    <div className="flex items-center gap-2 mb-1">
                      <Sparkles size={14} className="text-primary" />
                      <span className="text-[11px] font-bold tracking-[0.18em] text-primary uppercase">
                        Momentum Chain
                      </span>
                    </div>

                    <h2 className="text-3xl font-bold bg-gradient-to-br from-gray-900 to-gray-600 bg-clip-text text-transparent mb-2 leading-tight">
                      {canvasData.data.title || "Your Momentum Map"}
                    </h2>
                    <p className="text-sm text-gray-500 mb-10">
                      {momentumDone
                        ? "Nice — today's link is locked in."
                        : "Anchor the new habit to something you already do."}
                    </p>

                    <div className="relative flex items-center justify-center gap-1 flex-wrap py-4">
                      {(canvasData.data.chain || canvasData.data.steps || canvasData.data.habits || []).map((step: any, idx: number) => {
                        const stepsArray = canvasData.data.chain || canvasData.data.steps || canvasData.data.habits || [];
                        const isLast = idx === stepsArray.length - 1;

                        return (
                          <div key={idx} className="flex items-center">
                            <div className="flex flex-col items-center gap-3">
                              <div
                                className={`relative flex items-center justify-center w-20 h-20 rounded-full transition-all duration-700 ${
                                  momentumDone
                                    ? "bg-gradient-to-br from-primary to-primary/70 shadow-xl shadow-primary/40 scale-110"
                                    : "bg-white border-2 border-gray-200 shadow-sm"
                                }`}
                                style={momentumDone ? ({ animation: "momentumGlow 2s ease-in-out infinite" } as React.CSSProperties) : undefined}
                              >
                                <span className={`text-3xl transition-transform duration-500 ${momentumDone ? "scale-110" : ""}`}>
                                  {step.icon || "🔗"}
                                </span>
                                {momentumDone && (
                                  <div className="absolute -top-1 -right-1 bg-white rounded-full p-0.5 shadow-md">
                                    <CheckCircle2 size={16} className="text-primary" fill="white" />
                                  </div>
                                )}
                              </div>
                              <span
                                className={`text-[11px] font-semibold text-center leading-tight max-w-[76px] transition-colors duration-500 ${
                                  momentumDone ? "text-gray-900" : "text-gray-500"
                                }`}
                              >
                                {step.label}
                              </span>
                            </div>

                            {!isLast && (
                              <div className="relative w-10 h-[3px] mx-1 mb-6 rounded-full bg-gray-200 overflow-hidden">
                                <div
                                  className={`absolute inset-0 rounded-full transition-all duration-700 ${
                                    momentumDone ? "bg-gradient-to-r from-primary/40 via-primary to-primary/40" : "bg-transparent"
                                  }`}
                                />
                                {momentumDone && (
                                  <div
                                    className="absolute top-0 h-full w-4 rounded-full bg-white/90 blur-[2px]"
                                    style={{ animation: "momentumSpark 1.4s ease-in-out infinite", animationDelay: `${idx * 0.15}s` }}
                                  />
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    <div className="flex justify-center mt-8">
                      <button
                        disabled={momentumDone}
                        onClick={() => {
                          setMomentumDone(true);
                          submitCanvasResult({
                            completed: true,
                            date: new Date().toISOString().slice(0, 10),
                          });
                        }}
                        className={`group flex items-center gap-2.5 px-8 py-3.5 rounded-full font-bold text-sm tracking-wide transition-all duration-300 ${
                          momentumDone
                            ? "bg-primary/10 text-primary cursor-default"
                            : "bg-gradient-to-r from-primary to-primary/80 text-white shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/35 hover:-translate-y-0.5"
                        }`}
                      >
                        {momentumDone ? (
                          <>
                            <CheckCircle2 size={18} />
                            Done for today
                          </>
                        ) : (
                          <>
                            <Sparkles size={16} className="transition-transform group-hover:rotate-12" />
                            Mark today's link done
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}

                {canvasData.type === "canvas_show_text" && (
                  <div>
                    <h2 className="text-3xl font-bold text-gray-900 mb-6">{canvasData.data.title}</h2>
                    <div className="prose prose-lg text-gray-700 whitespace-pre-wrap">
                      {canvasData.data.body}
                    </div>
                  </div>
                )}

                {canvasData.type === "canvas_show_question" && (
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-8">{canvasData.data.question}</h2>
                    <div className="space-y-4">
                      {canvasData.data.options?.map((opt: any) => (
                        <button
                          key={opt.id}
                          onClick={() => {
                            submitCanvasResult({ answer: opt.id });
                          }}
                          className="w-full text-left p-4 rounded-xl border-2 border-gray-100 hover:border-primary hover:bg-primary/5 transition-all text-lg font-medium text-gray-800"
                        >
                          <span className="inline-block w-8 font-bold text-primary">{opt.id.toUpperCase()}.</span>
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {canvasData.type === "canvas_show_chart" && (
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">{canvasData.data.title}</h2>
                    <div className="flex flex-col gap-4 mt-6 p-4 bg-gray-50 rounded-xl border border-gray-100">
                      {canvasData.data.data?.map((item: any, idx: number) => {
                        const maxVal = Math.max(...canvasData.data.data.map((d: any) => d.value || 0));
                        const widthPct = maxVal > 0 ? (item.value / maxVal) * 100 : 0;
                        return (
                          <div key={idx} className="flex items-center gap-4">
                            <div className="w-1/4 text-right font-medium text-gray-700">{item.label}</div>
                            <div className="flex-1 h-6 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-primary rounded-full transition-all duration-1000 ease-out"
                                style={{ width: `${widthPct}%` }}
                              />
                            </div>
                            <div className="w-16 font-bold text-gray-900">{item.value}</div>
                          </div>
                        );
                      })}
                    </div>
                    <p className="text-sm text-gray-500 mt-4 text-center italic">{canvasData.data.x_label} vs {canvasData.data.y_label}</p>
                  </div>
                )}

                {canvasData.type === "canvas_show_input" && (
                  <form
                    onSubmit={(event) => {
                      event.preventDefault();
                      const value = (event.currentTarget.elements.namedItem("inputValue") as HTMLInputElement).value;
                      submitCanvasResult({ value });
                    }}
                  >
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">{canvasData.data.prompt || canvasData.data.title || "Please enter:"}</h2>
                    <input
                      name="inputValue"
                      type={canvasData.data.input_type || "text"}
                      className="w-full border-2 border-gray-200 rounded-xl p-4 text-lg outline-none focus:border-primary"
                      placeholder={canvasData.data.placeholder || "Your answer..."}
                      autoFocus
                    />
                    <div className="mt-6 flex justify-end gap-3">
                      <button type="button" onClick={() => setCanvasVisible(false)} className="px-6 py-3 rounded-xl font-medium text-gray-500 hover:bg-gray-100">Cancel</button>
                      <button type="submit" className="px-6 py-3 rounded-xl font-bold text-white bg-primary hover:bg-primary/90">Submit</button>
                    </div>
                  </form>
                )}

                {canvasData.type === "canvas_show_alert" && (
                  <div>
                    <div className="flex items-center gap-4 mb-6">
                      <div className="bg-amber-100 p-3 rounded-full text-amber-600">
                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <h2 className="text-2xl font-bold text-gray-900">{canvasData.data.title || "Alert"}</h2>
                    </div>
                    <p className="text-lg text-gray-700 mb-8">{canvasData.data.message || canvasData.data.body}</p>
                    <div className="flex justify-end">
                      <button onClick={() => setCanvasVisible(false)} className="px-8 py-3 rounded-xl font-bold text-white bg-primary hover:bg-primary/90">Dismiss</button>
                    </div>
                  </div>
                )}

                {(canvasData.type === "canvas_show_scheduling_embed" || canvasData.type === "canvas_show_calendar") && (
                  <div className="flex flex-col h-[600px]">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">{canvasData.data.title || "Schedule a Session"}</h2>
                    {canvasData.data.url ? (
                      <iframe
                        src={canvasData.data.url}
                        className="flex-1 w-full rounded-xl border border-gray-200"
                        title="Scheduling Embed"
                      />
                    ) : (
                      <div className="flex-1 w-full rounded-xl border border-dashed border-gray-300 flex items-center justify-center bg-gray-50">
                        <p className="text-gray-500 font-medium">Calendar widget would appear here.</p>
                      </div>
                    )}
                    <div className="mt-4 flex justify-end">
                      <button onClick={() => setCanvasVisible(false)} className="px-6 py-2 rounded-lg font-medium text-gray-600 hover:bg-gray-100 border border-gray-200">Close</button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className={`absolute top-24 right-6 w-64 h-36 bg-gray-900 rounded-2xl overflow-hidden shadow-2xl border border-white/10 z-20 transition-opacity duration-500 ${showControls ? "opacity-100" : "opacity-40"}`}>
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover -scale-x-100 transition-opacity duration-300 ${isCameraOn ? "opacity-100" : "opacity-0"}`}
            />
            {!isCameraOn && (
              <div className="absolute inset-0 flex items-center justify-center text-gray-500 bg-gray-800">
                <VideoOff size={28} />
              </div>
            )}
          </div>

          <div className={`absolute bottom-8 left-1/2 transform -translate-x-1/2 flex items-center gap-4 bg-gray-900/70 backdrop-blur-xl border border-white/10 px-8 py-4 rounded-full z-20 shadow-2xl transition-all duration-500 ${showControls ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0 pointer-events-none"}`}>
            <button
              onClick={toggleMic}
              className={`p-4 rounded-full transition-all shadow-lg ${isMicOn ? "bg-white/10 hover:bg-white/20 text-white" : "bg-red-500 hover:bg-red-600 text-white"}`}
            >
              {isMicOn ? <Mic size={22} /> : <MicOff size={22} />}
            </button>

            <button
              onClick={toggleCamera}
              className={`p-4 rounded-full transition-all shadow-lg ${isCameraOn ? "bg-white/10 hover:bg-white/20 text-white" : "bg-red-500 hover:bg-red-600 text-white"}`}
            >
              {isCameraOn ? <Video size={22} /> : <VideoOff size={22} />}
            </button>

            <div className="w-px h-10 bg-white/20 mx-2" />

            <button
              onClick={handleEndConversation}
              disabled={loading}
              className="px-8 py-4 bg-red-600 hover:bg-red-700 text-white rounded-full font-bold shadow-lg transition-colors flex items-center gap-3 disabled:opacity-50"
            >
              <PhoneOff size={22} />
              {loading ? "Ending..." : "End Call"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}