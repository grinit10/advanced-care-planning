import { useState, FormEvent } from "react";
import { SparklesFullPage } from "./ui/SparklesCore";

interface PreJoinProps {
  onJoin: (roomName: string, identity: string) => void;
  connecting: boolean;
}

export default function PreJoin({ onJoin, connecting }: PreJoinProps) {
  const [name, setName] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    // Generate a unique room name per conversation to isolate sessions
    const uniqueRoom = `acp-room-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
    onJoin(uniqueRoom, name.trim());
  };

  return (
    <SparklesFullPage className="prejoin">
      <div className="prejoin-card">
        <h1>Advanced Care Planning</h1>
        <p className="prejoin-subtitle">
          Have a private conversation with an AI assistant about your future
          healthcare wishes. Your voice stays on your device — nothing is
          recorded or shared.
        </p>

        <form onSubmit={handleSubmit} className="prejoin-form">
          <label htmlFor="name-input">Your name</label>
          <input
            id="name-input"
            type="text"
            placeholder="Enter your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={connecting}
            autoFocus
          />

          <button type="submit" disabled={!name.trim() || connecting}>
            {connecting ? "Connecting..." : "Start Conversation"}
          </button>
        </form>

        <p className="prejoin-note">
          You'll need a microphone and speakers. Make sure your browser has
          permission to use them.
        </p>
      </div>
    </SparklesFullPage>
  );
}