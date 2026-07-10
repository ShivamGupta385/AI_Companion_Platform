"use client";

import { useEffect, useState, useRef } from "react";
import { tavusService } from "@/services/tavus.service";
import DailyIframe, { DailyCall } from "@daily-co/daily-js";
import { Mic, MicOff, Video, VideoOff, PhoneOff, Maximize, Minimize, Signal, Activity } from "lucide-react";

interface Props {
  companionId: string;
}

export default function TavusAvatar({
  companionId,
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

  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const controlsTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup on unmount if a session is active
  useEffect(() => {
    return () => {
      if (currentConversationId) {
        tavusService.endSession(currentConversationId).catch(console.error);
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
      
      // Initialize headless Daily call object with local video and audio
      const call = DailyIframe.createCallObject({
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
        await tavusService.endSession(currentConversationId);
      } catch (backendErr) {
        console.warn("Backend end session failed or already ended:", backendErr);
      }

      // Hide UI immediately
      setSessionActive(false);
      setCurrentConversationId("");
      setIsMicOn(true);
      setIsCameraOn(true);
      setAgentState("listening");
      
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

  return (
    <div className={`flex flex-col w-full rounded-3xl bg-white overflow-hidden shadow-sm relative ${sessionActive ? 'h-full' : 'h-162.5'}`}>
      {!sessionActive ? (
        <div className="flex flex-col flex-1 items-center justify-center p-6 text-center">
          <h3 className="text-2xl font-bold mb-4 text-gray-800">Ready to chat with Aria?</h3>
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
                 <span>{agentState === "speaking" ? "Aria is speaking..." : "Aria is listening..."}</span>
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
            className={`w-full h-full object-cover transition-all duration-300 ${agentState === "speaking" ? "ring-2 ring-primary/30" : ""}`}
          />
          <audio ref={audioRef} autoPlay />

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