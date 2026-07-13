import { useEffect, useRef } from "react";

export interface TranscriptMessage {
  id: number;
  role: "agent" | "user";
  text: string;
}

interface TranscriptPanelProps {
  messages: TranscriptMessage[];
}

export default function TranscriptPanel({ messages }: TranscriptPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="transcript">
      {messages.length === 0 && (
        <div className="transcript-empty">
          <p>Your conversation will appear here.</p>
          <p className="text-muted">
            Speak when you're ready — the assistant will respond.
          </p>
        </div>
      )}

      {messages.map((msg) => (
        <div key={msg.id} className={`transcript-msg msg-${msg.role}`}>
          <span className="msg-label">
            {msg.role === "agent" ? "Assistant" : "You"}
          </span>
          <p>{msg.text}</p>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}