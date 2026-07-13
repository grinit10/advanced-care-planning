import { useState } from "react";
import TranscriptPanel, { TranscriptMessage } from "./TranscriptPanel";

interface ConversationViewProps {
  transcript: TranscriptMessage[];
  onRegisterEmail: (email: string) => Promise<{ success: boolean; message: string }>;
  onSendPlan: () => Promise<{ status: string; message: string }>;
  onCloseSession: () => Promise<{ success: boolean; message: string }>;
  onDisconnect: () => void;
}

type PanelMode = "conversation" | "plan";

export default function ConversationView({
  transcript,
  onRegisterEmail,
  onSendPlan,
  onCloseSession,
  onDisconnect,
}: ConversationViewProps) {
  const [mode, setMode] = useState<PanelMode>("conversation");
  const [email, setEmail] = useState("");
  const [emailStatus, setEmailStatus] = useState<string | null>(null);
  const [sendStatus, setSendStatus] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [closing, setClosing] = useState(false);

  // Double-check before closing
  const [confirmClose, setConfirmClose] = useState(false);

  const handleRegisterEmail = async () => {
    if (!email.trim()) return;
    setEmailStatus(null);
    const result = await onRegisterEmail(email.trim());
    setEmailStatus(result.message);
    if (result.success) {
      setEmail("");
    }
  };

  const handleSendPlan = async () => {
    setSending(true);
    setSendStatus(null);
    const result = await onSendPlan();
    setSendStatus(result.message);
    setSending(false);
  };

  const handleCloseSession = async () => {
    if (!confirmClose) {
      setConfirmClose(true);
      return;
    }
    setClosing(true);
    await onCloseSession();
  };

  if (mode === "plan") {
    return (
      <div className="conversation">
        <div className="plan-panel">
          <h2>Your ACP Session</h2>
          <p className="text-muted">
            Your conversation data is stored locally. Add your email to receive the
            plan summary and voice recording, then close the session when done.
          </p>

          {/* Email registration */}
          <div className="plan-section">
            <h3>1. Add your email</h3>
            <div className="email-row">
              <input
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleRegisterEmail()}
              />
              <button onClick={handleRegisterEmail}>Register</button>
            </div>
            {emailStatus && (
              <p className={`plan-msg ${emailStatus.includes("fail") || emailStatus.includes("Error") ? "msg-error" : "msg-ok"}`}>
                {emailStatus}
              </p>
            )}
          </div>

          {/* Send plan */}
          <div className="plan-section">
            <h3>2. Send plan to email</h3>
            <p className="text-muted">
              Receive your conversation summary, preferences, and voice recording
              via email. Requires Azure Communication Services configured in .env.
            </p>
            <button onClick={handleSendPlan} disabled={sending}>
              {sending ? "Sending..." : "Send Plan"}
            </button>
            {sendStatus && (
              <p className={`plan-msg ${sendStatus.includes("fail") || sendStatus.includes("Error") ? "msg-error" : "msg-ok"}`}>
                {sendStatus}
              </p>
            )}
          </div>

          {/* Close session */}
          <div className="plan-section">
            <h3>3. Close session</h3>
            <p className="text-muted">
              This deletes your conversation data and audio recording from the
              server. You can send the plan to email first.
            </p>
            <button
              className="btn-close"
              onClick={handleCloseSession}
              disabled={closing}
            >
              {closing
                ? "Closing..."
                : confirmClose
                  ? "Confirm — delete my data"
                  : "Close Session"}
            </button>
            {confirmClose && !closing && (
              <p className="plan-msg msg-warn">
                Click again to confirm. This cannot be undone.
              </p>
            )}
          </div>

          <button className="btn-back" onClick={() => { setMode("conversation"); setConfirmClose(false); }}>
            Back to conversation
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="conversation">
      <header className="conversation-header">
        <div className="conversation-status">
          <span className="status-dot" />
          <span>Assistant is listening...</span>
        </div>
        <div className="header-actions">
          <button className="btn-plan" onClick={() => setMode("plan")}>
            Session Plan
          </button>
          <button className="btn-end" onClick={onDisconnect}>
            End Conversation
          </button>
        </div>
      </header>

      <TranscriptPanel messages={transcript} />

      <footer className="conversation-footer">
        <div className="mic-indicator">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <rect x="9" y="2" width="6" height="11" rx="3" />
            <path d="M5 10a7 7 0 0 0 14 0" />
            <line x1="12" y1="19" x2="12" y2="22" />
          </svg>
          <span>Mic active — speak freely</span>
        </div>
      </footer>
    </div>
  );
}