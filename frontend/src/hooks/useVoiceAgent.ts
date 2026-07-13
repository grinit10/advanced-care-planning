import { useState, useCallback, useRef } from "react";
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
  const [transcript, setTranscript] = useState<TranscriptMessage[]>([]);
  const [roomId, setRoomId] = useState<string>("");
  const roomRef = useRef<Room | null>(null);

  const addTranscript = useCallback(
    (msg: TranscriptMessage) => {
      setTranscript((prev) => [...prev, msg]);
    },
    []
  );

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
        });

        room.on(RoomEvent.TrackSubscribed, (track) => {
          if (track.kind === "audio") {
            // Play agent's voice by attaching audio track to an <audio> element
            const audioEl = document.createElement("audio");
            audioEl.id = "agent-audio";
            audioEl.autoplay = true;
            track.attach(audioEl);
            document.body.appendChild(audioEl);
          }
        });

        room.on(RoomEvent.TrackUnsubscribed, (track) => {
          if (track.kind === "audio") {
            const audioEl = document.getElementById("agent-audio") as HTMLMediaElement | null;
            if (audioEl) {
              track.detach(audioEl);
              audioEl.remove();
            }
          }
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
    roomRef.current?.disconnect();
    roomRef.current = null;
    setConnected(false);
    setRoomId("");
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
    transcript,
    roomId,
    connect,
    disconnect,
    registerEmail,
    sendPlan,
    closeSession,
  };
}