"use client";

import { useEffect, useState, useRef } from "react";
import { tavusService } from "@/services/tavus.service";
import DailyIframe, { DailyCall } from "@daily-co/daily-js";
import { Mic, MicOff, Video, VideoOff, PhoneOff, Maximize, Minimize, Signal, Activity } from "lucide-react";

interface Props {
  companionId: string;
  companionName?: string;
}

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

  // New states for UI enhancements
  const [callDuration, setCallDuration] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [agentState, setAgentState] = useState<"listening" | "speaking" | "thinking">("listening");
  const [canvasData, setCanvasData] = useState<{ type: string; data: any; tool_call_id?: string } | null>(null);
  const [canvasVisible, setCanvasVisible] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const controlsTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const durationRef = useRef<number>(0);

  // Cleanup on unmount if a session is active
  useEffect(() => {
    return () => {
      if (currentConversationId) {
        tavusService.endSession(currentConversationId, durationRef.current).catch(console.error);
      }
      if (callObject) {
        callObject.leave().then(() => callObject.destroy());
      }
      if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current);
    };
  }, [currentConversationId, callObject]);

  // Call Duration Timer
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (sessionActive) {
      interval = setInterval(() => {
        setCallDuration((prev) => {
          const newDuration = prev + 1;
          durationRef.current = newDuration;
          return newDuration;
        });
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

  // Fullscreen Listener
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
    setLoading(true);
    try {
      const session = await tavusService.createSession(companionId);
      console.log(session);
      setCurrentConversationId(session.conversation_id);
      
      // Ensure any existing headless Daily call object is destroyed or reused
      let call = DailyIframe.getCallInstance();
      if (call) {
        await call.destroy();
      }
      
      call = DailyIframe.createCallObject({
        audioSource: true,
        videoSource: true,
      });
      setCallObject(call);

      // Listen for active speaker changes
      call.on("active-speaker-change", (e) => {
        if (e.activeSpeaker?.peerId === call.participants().local.session_id) {
          setAgentState("listening");
        } else {
          setAgentState("speaking");
        }
      });

      // The most reliable way to bind local and remote tracks is participant-updated
      call.on("participant-updated", (e) => {
        const p = e.participant;
        
        // Local participant video
        if (p.local && p.tracks.video?.state === "playable" && p.tracks.video.persistentTrack && localVideoRef.current) {
          const stream = localVideoRef.current.srcObject as MediaStream;
          if (!stream || !stream.getTracks().includes(p.tracks.video.persistentTrack)) {
            localVideoRef.current.srcObject = new MediaStream([p.tracks.video.persistentTrack]);
          }
        }

        // Remote participant (Avatar) video and audio
        if (!p.local) {
          if (p.tracks.video?.state === "playable" && p.tracks.video.persistentTrack && videoRef.current) {
            const stream = videoRef.current.srcObject as MediaStream;
            if (!stream || !stream.getTracks().includes(p.tracks.video.persistentTrack)) {
              videoRef.current.srcObject = new MediaStream([p.tracks.video.persistentTrack]);
            }
          }
          if (p.tracks.audio?.state === "playable" && p.tracks.audio.persistentTrack && audioRef.current) {
            const stream = audioRef.current.srcObject as MediaStream;
            if (!stream || !stream.getTracks().includes(p.tracks.audio.persistentTrack)) {
              audioRef.current.srcObject = new MediaStream([p.tracks.audio.persistentTrack]);
            }
          }
        }
      });

      // Listen for Magic Canvas tool calls from Tavus
      call.on("app-message", (e: any) => {
        try {
          const payload = typeof e.data === 'string' ? JSON.parse(e.data) : e.data;
          console.log("APP_MESSAGE:", payload);
          
          // Deep search function to find any object that looks like a tool call for the canvas
          const findCanvasToolCall = (obj: any, depth = 0): { name: string, args: any, id?: string } | null => {
            if (depth > 10) return null; // Prevent infinite recursion
            
            // If it's a string that looks like JSON, try to parse it
            if (typeof obj === 'string') {
               const trimmed = obj.trim();
               if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
                 try {
                   const parsed = JSON.parse(trimmed);
                   return findCanvasToolCall(parsed, depth + 1);
                 } catch(e) {
                   return null;
                 }
               }
               return null;
            }

            // Helper to deeply parse arguments in case they are double or triple stringified
            const parseArgs = (rawArgs: any): any => {
              if (typeof rawArgs === 'string') {
                 try {
                   return parseArgs(JSON.parse(rawArgs));
                 } catch (e) {
                   return rawArgs;
                 }
              }
              return rawArgs || {};
            };

            if (!obj || typeof obj !== 'object') return null;

            // Handle raw OpenAI or simple tool call structure
            const name = obj.tool_name || obj.name || obj.function?.name;
            if (typeof name === 'string' && name.startsWith("canvas_show_")) {
              const argsStr = obj.arguments || obj.function?.arguments;
              const args = parseArgs(argsStr);
              return { name, args, id: obj.tool_call_id || obj.id };
            }

            // Handle native Tavus magic_canvas skill structure
            if (obj.component && typeof obj.component === 'string' && obj.component.startsWith('canvas.')) {
              // Ignore component registry meta-events sent by Tavus
              if (obj.mcp_server_url || obj.sandbox_url) {
                // Continue searching inside it just in case, but usually it's just meta
              } else {
                // Convert "canvas.question" back to "canvas_show_question" format for our UI
                const mappedName = obj.component.replace('canvas.', 'canvas_show_');
                return { name: mappedName, args: parseArgs(obj.data || obj.value || obj), id: obj.tool_call_id || obj.interaction_id || obj.id };
              }
            }
            
            if (name === "magic_canvas" && obj.arguments) {
              const args = parseArgs(obj.arguments);
              if (args.component) {
                 const mappedName = args.component.startsWith('canvas.') ? args.component.replace('canvas.', 'canvas_show_') : `canvas_show_${args.component}`;
                 return { name: mappedName, args: parseArgs(args.data || args.value || args), id: obj.tool_call_id || obj.id };
              }
            }
            
            // Search arrays
            if (Array.isArray(obj)) {
              for (const item of obj) {
                const res = findCanvasToolCall(item, depth + 1);
                if (res) return res;
              }
            } else {
              // Search nested objects
              for (const key in obj) {
                const res = findCanvasToolCall(obj[key], depth + 1);
                if (res) return res;
              }
            }
            return null;
          };

          const toolCall = findCanvasToolCall(payload);
          if (toolCall) {
            setCanvasData({ type: toolCall.name, data: toolCall.args, tool_call_id: toolCall.id });
            setCanvasVisible(true);
          }
        } catch(err) {
          console.error("Error parsing app-message", err);
        }
      });

      // Catch hardware errors (e.g. Cam In Use)
      call.on("camera-error", (e) => {
        console.error("Camera Error: Your webcam is currently in use by another application or blocked.", e);
        alert("Camera Error: Could not access your webcam. It might be in use by another app (like Zoom or OBS). Please close other video apps and try again.");
      });

      // Join the conversation URL as a headless client
      await call.join({ url: session.conversation_url });
      setSessionActive(true);
      setShowControls(true); // Ensure controls are shown on start
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Robustly bind tracks that might have fired before the DOM elements mounted
  useEffect(() => {
    if (sessionActive && callObject) {
      const participants = callObject.participants();
      
      // Bind local video if it exists
      if (participants.local?.tracks.video?.persistentTrack && localVideoRef.current) {
        const stream = localVideoRef.current.srcObject as MediaStream;
        if (!stream || !stream.getTracks().includes(participants.local.tracks.video.persistentTrack)) {
          localVideoRef.current.srcObject = new MediaStream([participants.local.tracks.video.persistentTrack]);
        }
      }
      
      // Bind remote tracks if they exist
      for (const p of Object.values(participants)) {
        if (p.local) continue;
        
        if (p.tracks.video?.persistentTrack && videoRef.current) {
          const stream = videoRef.current.srcObject as MediaStream;
          if (!stream || !stream.getTracks().includes(p.tracks.video.persistentTrack)) {
            videoRef.current.srcObject = new MediaStream([p.tracks.video.persistentTrack]);
          }
        }
        
        if (p.tracks.audio?.persistentTrack && audioRef.current) {
          const stream = audioRef.current.srcObject as MediaStream;
          if (!stream || !stream.getTracks().includes(p.tracks.audio.persistentTrack)) {
            audioRef.current.srcObject = new MediaStream([p.tracks.audio.persistentTrack]);
          }
        }
      }
    }
  }, [sessionActive, callObject]);

  const handleEndConversation = async () => {
    if (!currentConversationId) return;
    setLoading(true);
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen().catch(console.error);
      }
      
      // Attempt backend API call but don't let it block UI teardown
      try {
        await tavusService.endSession(currentConversationId, callDuration);
      } catch (backendErr) {
        console.warn("Backend end session failed or already ended:", backendErr);
      }

      // Hide UI immediately
      setSessionActive(false);
      setCurrentConversationId("");
      setIsMicOn(true);
      setIsCameraOn(true);
      setAgentState("listening");
      setCanvasData(null);
      setCanvasVisible(false);
      
      // Cleanup Daily call object safely
      if (callObject) {
        try {
          await callObject.leave();
          await callObject.destroy();
        } catch (dailyErr) {
          console.warn("Daily call object cleanup warning:", dailyErr);
        }
        setCallObject(null);
      }
      
      // Clear media streams
      if (videoRef.current) videoRef.current.srcObject = null;
      if (audioRef.current) audioRef.current.srcObject = null;
      if (localVideoRef.current) localVideoRef.current.srcObject = null;
    } catch (err) {
      console.error("Critical error in handleEndConversation:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleMic = () => {
    if (callObject) {
      const newState = !isMicOn;
      callObject.setLocalAudio(newState);
      setIsMicOn(newState);
    }
  };

  const toggleCamera = () => {
    if (callObject) {
      const newState = !isCameraOn;
      callObject.setLocalVideo(newState);
      setIsCameraOn(newState);
    }
  };

  const submitCanvasResult = (result: any) => {
    if (callObject) {
      // Find the label of the selected option for a natural spoken-like response
      let responseText = "";
      if (canvasData?.data?.options && result.answer) {
        const selectedOpt = canvasData.data.options.find((o: any) => o.id === result.answer);
        responseText = selectedOpt 
          ? `I choose: ${selectedOpt.label}` 
          : `My answer is: ${result.answer}`;
      } else {
        responseText = typeof result === 'string' ? result : JSON.stringify(result);
      }

      // Send as conversation.respond so the LLM receives it as user input
      const payload = {
        message_type: "conversation",
        event_type: "conversation.respond",
        conversation_id: currentConversationId,
        properties: {
          text: responseText
        }
      };
      console.log("[CANVAS SUBMIT]", JSON.stringify(payload));
      callObject.sendAppMessage(payload, '*');
    }
    setCanvasVisible(false);
  };

  return (
    <div className={`flex flex-col w-full rounded-3xl bg-white overflow-hidden shadow-sm relative ${sessionActive ? 'h-full' : 'h-162.5'}`}>
      {!sessionActive ? (
        <div className="flex flex-col flex-1 items-center justify-center p-6 text-center">
          <h3 className="text-2xl font-bold mb-4 text-gray-800">Ready to chat with {companionName || "your AI Companion"}?</h3>
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
          className="relative h-full w-full bg-black flex flex-col group min-h-[650px]"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setShowControls(false)}
        >
          
          {/* Top Bar: HD Signal, Timer, Maximize, and Agent Status */}
          <div className={`absolute top-0 left-0 w-full p-6 flex justify-between items-start z-20 transition-opacity duration-500 ${showControls ? "opacity-100" : "opacity-0"}`}>
            
            {/* Top Left Stack */}
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
              
              {/* Agent Badge (moved below HD & Timer) */}
              <div className="flex items-center gap-2 bg-black/40 backdrop-blur-md px-4 py-2 rounded-full text-white text-sm font-medium shadow-lg transition-all duration-300 w-max">
                 <Activity size={16} className={agentState === "speaking" ? "text-green-400 animate-pulse" : "text-gray-400"} />
                 <span>{agentState === "speaking" ? `${companionName || "Companion"} is speaking...` : `${companionName || "Companion"} is listening...`}</span>
              </div>
            </div>
            
            <button onClick={toggleFullscreen} className="bg-black/40 backdrop-blur-md p-3 rounded-full text-white hover:bg-black/60 transition">
              {isFullscreen ? <Minimize size={20} /> : <Maximize size={20} />}
            </button>
          </div>

          {/* Avatar Video */}
          <video 
            ref={videoRef}
            autoPlay 
            playsInline
            className={`flex-1 w-full h-full object-cover transition-all duration-300 ${agentState === "speaking" ? "ring-2 ring-primary/30" : ""}`}
          />
          <audio ref={audioRef} autoPlay />

          {/* Magic Canvas Overlay */}
          {canvasVisible && canvasData && (
            <div className="absolute inset-0 flex items-center justify-center p-8 z-30 pointer-events-none">
              <div className="bg-white/95 backdrop-blur-xl p-8 rounded-3xl shadow-2xl max-w-2xl w-full border border-gray-200 pointer-events-auto transform transition-all duration-500 scale-100 opacity-100">
                <button 
                  onClick={() => setCanvasVisible(false)}
                  className="absolute top-4 right-4 text-gray-500 hover:text-gray-800 p-2"
                >
                  ✕
                </button>
                
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
                    {canvasData.data.question ? (
                      <>
                        <h2 className="text-2xl font-bold text-gray-900 mb-8">{canvasData.data.question}</h2>
                        <div className="space-y-4">
                          {canvasData.data.options?.map((opt: any, idx: number) => (
                            <button
                              key={opt.id}
                              onClick={() => {
                                submitCanvasResult({ selected_option_ids: [opt.id], answer: opt.id });
                              }}
                              className="w-full text-left p-4 rounded-xl border-2 border-gray-100 hover:border-primary hover:bg-primary/5 transition-all text-lg font-medium text-gray-800"
                            >
                              <span className="inline-block w-8 font-bold text-primary">{String.fromCharCode(65 + idx)}.</span>
                              {opt.label}
                            </button>
                          ))}
                        </div>
                      </>
                    ) : (
                      <div className="p-4 bg-red-50 text-red-800 border border-red-200 rounded-xl overflow-auto text-xs font-mono max-h-96">
                        <strong>Missing expected 'question' field. Payload structure:</strong><br/><br/>
                        {JSON.stringify(canvasData.data, null, 2)}
                      </div>
                    )}
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
                  <form onSubmit={(e) => {
                    e.preventDefault();
                    const val = (e.currentTarget.elements.namedItem('inputValue') as HTMLInputElement).value;
                    submitCanvasResult({ value: val });
                  }}>
                    <h2 className="text-2xl font-bold text-gray-900 mb-6">{canvasData.data.title || "Please provide input"}</h2>
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

          {/* Local User Video (Picture-in-Picture) */}
          <div className={`absolute top-24 right-6 w-64 h-36 bg-gray-900 rounded-2xl overflow-hidden shadow-2xl border border-white/10 z-20 transition-opacity duration-500 ${showControls ? "opacity-100" : "opacity-40"}`}>
            <video 
              ref={localVideoRef}
              autoPlay 
              playsInline
              muted
              className={`w-full h-full object-cover -scale-x-100 transition-opacity duration-300 ${isCameraOn ? 'opacity-100' : 'opacity-0'}`}
            />
            {!isCameraOn && (
              <div className="absolute inset-0 flex items-center justify-center text-gray-500 bg-gray-800">
                <VideoOff size={28} />
              </div>
            )}
          </div>

          {/* Glassmorphism Control Bar Overlay */}
          <div className={`absolute bottom-8 left-1/2 transform -translate-x-1/2 flex items-center gap-4 bg-gray-900/70 backdrop-blur-xl border border-white/10 px-8 py-4 rounded-full z-20 shadow-2xl transition-all duration-500 ${showControls ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0 pointer-events-none"}`}>
            <button 
              onClick={toggleMic}
              className={`p-4 rounded-full transition-all shadow-lg ${isMicOn ? 'bg-white/10 hover:bg-white/20 text-white' : 'bg-red-500 hover:bg-red-600 text-white'}`}
            >
              {isMicOn ? <Mic size={22} /> : <MicOff size={22} />}
            </button>

            <button 
              onClick={toggleCamera}
              className={`p-4 rounded-full transition-all shadow-lg ${isCameraOn ? 'bg-white/10 hover:bg-white/20 text-white' : 'bg-red-500 hover:bg-red-600 text-white'}`}
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