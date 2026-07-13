import { useState, useCallback, useRef, useEffect } from "react";
import { Room, RoomEvent, createLocalAudioTrack } from "livekit-client";

const LIVEKIT_URL = import.meta.env.VITE_LIVEKIT_URL ?? "ws://localhost:7880";
const TOKEN_SERVER_URL =
  import.meta.env.VITE_TOKEN_SERVER_URL ?? "http://localhost:8081";
const AGENT_API_URL =
  import.meta.env.VITE_AGENT_API_URL ?? "http://localhost:8082";

export interface TranscriptMessage {
  id: number;
  role: "agent" | "user";
  text: string;
}

export interface PlanResult {
  summary: string;
  preferences: Record<string, string>;
  email_count: number;
}

export interface SendResult {
  status: "sent" | "partial" | "error";
  message: string;
}

/**
 * Hook that manages a LiveKit room connection + ACP session API calls.
 */
export function useVoiceAgent() {
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [agentSpeaking, setAgentSpeaking] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptMessage[]>([]);
  const [roomId, setRoomId] = useState<string>("");
  const [preferences, setPreferences] = useState<Record<string, unknown>>({});
  const roomRef = useRef<Room | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Clean up polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
      }
    };
  }, []);

  const addTranscript = useCallback(
    (msg: TranscriptMessage) => {
      setTranscript((prev) => [...prev, msg]);
    },
    []
  );

  const fetchTranscript = useCallback(async (currentRoomId: string) => {
    try {
      const res = await fetch(
        `${AGENT_API_URL}/transcript-json/${encodeURIComponent(currentRoomId)}`
      );
      if (res.ok) {
        const data = await res.json();
        if (data.transcript && Array.isArray(data.transcript)) {
          setTranscript((prev) => {
            // Only update if there are new entries
            if (data.transcript.length <= prev.length) return prev;
            return data.transcript.map((entry: { role: string; text: string }, idx: number) => ({
              id: idx + 1,
              role: entry.role as "agent" | "user",
              text: entry.text,
            }));
          });
        }
      }
    } catch {
      // Silently fail — polling will retry
    }
  }, []);

  const fetchPreferences = useCallback(async (currentRoomId: string) => {
    try {
      const res = await fetch(
        `${AGENT_API_URL}/preferences/${encodeURIComponent(currentRoomId)}`
      );
      if (res.ok) {
        const data = await res.json();
        if (data.preferences && Object.keys(data.preferences).length > 0) {
          setPreferences(data.preferences);
        }
      }
    } catch {
      // Silently fail — polling will retry
    }
  }, []);

  const startPolling = useCallback((currentRoomId: string) => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
    }
    // Poll every 3 seconds for live transcript and preference updates
    pollRef.current = setInterval(() => {
      fetchTranscript(currentRoomId);
      fetchPreferences(currentRoomId);
    }, 3000);
    // Also fetch immediately
    fetchTranscript(currentRoomId);
    fetchPreferences(currentRoomId);
  }, [fetchTranscript, fetchPreferences]);

  const connect = useCallback(
    async (roomName: string, identity: string) => {
      setConnecting(true);
      try {
        const res = await fetch(
          `${TOKEN_SERVER_URL}/token?room=${encodeURIComponent(roomName)}&identity=${encodeURIComponent(identity)}`
        );
        if (!res.ok) {
          throw new Error(`Token server error: ${res.statusText}`);
        }
        const { token } = await res.json();

        const room = new Room({
          adaptiveStream: true,
          dynacast: true,
        });

        room.on(RoomEvent.Disconnected, () => {
          setConnected(false);
          setTranscript([]);
        });

        room.on(RoomEvent.TrackSubscribed, (track) => {
          if (track.kind === "audio") {
            // Play agent's voice by attaching audio track to an <audio> element
            const audioEl = document.createElement("audio");
            audioEl.id = `agent-audio-${track.sid}`;
            audioEl.autoplay = true;
            track.attach(audioEl);
            document.body.appendChild(audioEl);
          }
        });

        room.on(RoomEvent.TrackUnsubscribed, (track) => {
          if (track.kind === "audio") {
            const audioEl = document.getElementById(`agent-audio-${track.sid}`) as HTMLMediaElement | null;
            if (audioEl) {
              track.detach(audioEl);
              audioEl.remove();
            }
          }
        });

        // Detect when the agent is speaking via active speaker changes
        room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
          const agentSpeaker = speakers.find((p) => p.identity?.startsWith("agent-"));
          setAgentSpeaking(!!agentSpeaker);
        });

        await room.connect(LIVEKIT_URL, token);

        // Publish the user's microphone audio so the agent can hear them
        try {
          const micTrack = await createLocalAudioTrack();
          await room.localParticipant.publishTrack(micTrack);
        } catch (micErr) {
          console.warn("Microphone access denied:", micErr);
          // The agent will still be able to speak even without mic input
        }

        roomRef.current = room;
        setRoomId(roomName);
        setConnected(true);

        // Start polling for live preferences
        setPreferences({});
        startPolling(roomName);

        addTranscript({
          id: Date.now(),
          role: "agent",
          text: "Connecting you to the Advanced Care Planning assistant...",
        });
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        addTranscript({ id: Date.now(), role: "agent", text: `Error: ${message}` });
        throw err;
      } finally {
        setConnecting(false);
      }
    },
    [addTranscript]
  );

  const disconnect = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    roomRef.current?.disconnect();
    roomRef.current = null;
    setConnected(false);
    setRoomId("");
    setPreferences({});
  }, []);

  // --- Session API calls ---

  const registerEmail = useCallback(
    async (email: string): Promise<{ success: boolean; message: string }> => {
      if (!roomId) return { success: false, message: "No active session." };
      try {
        const res = await fetch(
          `${AGENT_API_URL}/email/${encodeURIComponent(roomId)}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
          }
        );
        const data = await res.json();
        return { success: res.ok, message: data.message || data.error || "OK" };
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        return { success: false, message: msg };
      }
    },
    [roomId]
  );

  const sendPlan = useCallback(async (): Promise<SendResult> => {
    if (!roomId) return { status: "error", message: "No active session." };
    try {
      const res = await fetch(
        `${AGENT_API_URL}/send-plan/${encodeURIComponent(roomId)}`,
        { method: "POST" }
      );
      const data = await res.json();
      if (!res.ok) {
        return { status: "error", message: data.error || "Failed to send." };
      }
      return { status: data.status, message: data.message };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      return { status: "error", message: msg };
    }
  }, [roomId]);

  const closeSession = useCallback(async (): Promise<{ success: boolean; message: string }> => {
    if (!roomId) return { success: false, message: "No active session." };
    try {
      const res = await fetch(
        `${AGENT_API_URL}/close/${encodeURIComponent(roomId)}`,
        { method: "POST" }
      );
      const data = await res.json();
      disconnect();
      return { success: res.ok, message: data.message || "Session closed." };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      disconnect();
      return { success: true, message: msg };
    }
  }, [roomId, disconnect]);

  return {
    connecting,
    connected,
    agentSpeaking,
    transcript,
    preferences,
    roomId,
    connect,
    disconnect,
    registerEmail,
    sendPlan,
    closeSession,
  };
}