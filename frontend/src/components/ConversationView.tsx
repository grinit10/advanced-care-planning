import { useState } from "react";
import { TranscriptMessage } from "../hooks/useVoiceAgent";
import TranscriptPanel from "./TranscriptPanel";

const AGENT_API_URL = import.meta.env.VITE_AGENT_API_URL ?? "http://localhost:8082";

interface ConversationViewProps {
  transcript: TranscriptMessage[];
  agentSpeaking: boolean;
  preferences: Record<string, unknown>;
  planSummary: string;
  roomId: string;
  onRegisterEmail: (email: string) => Promise<{ success: boolean; message: string }>;
  onSendPlan: () => Promise<{ status: string; message: string }>;
  onCloseSession: () => Promise<{ success: boolean; message: string }>;
  onDisconnect: () => void;
  connected: boolean;
}

type PanelMode = "conversation" | "plan";

export default function ConversationView({
  transcript,
  agentSpeaking,
  preferences,
  roomId,
  onRegisterEmail,
  onSendPlan,
  onCloseSession,
  onDisconnect,
  connected,
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

  const handleDownloadTranscript = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    window.open(`${AGENT_API_URL}/transcript/${encodeURIComponent(roomId)}`, "_blank");
  };

  if (mode === "plan" || !connected) {
    return (
      <div className="conversation-container">
        <div className="plan-panel">
          <h2>Your ACP Session</h2>
          {!connected && (
            <p
              className="call-ended-notice"
              style={{
                padding: "12px 16px",
                background: "rgba(239, 68, 68, 0.08)",
                color: "#ef4444",
                border: "1px solid rgba(239, 68, 68, 0.15)",
                borderRadius: "8px",
                fontSize: "0.9rem",
                fontWeight: "500",
                marginBottom: "16px",
              }}
            >
              🔴 Conversation ended. Your transcript and recording have been compiled.
            </p>
          )}
          <p className="text-muted">
            Your conversation data is stored in Redis (inside Docker). Add your email to receive the
            plan summary and voice recording, then close the session to delete all data.
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
              <p
                className={`plan-msg ${emailStatus.includes("fail") || emailStatus.includes("Error") ? "msg-error" : "msg-ok"}`}
              >
                {emailStatus}
              </p>
            )}
          </div>

          {/* Send plan */}
          <div className="plan-section">
            <h3>2. Send plan to email</h3>
            <p className="text-muted">
              Receive your conversation summary, preferences, and voice recording via email.
              Requires Azure Communication Services configured in .env.
            </p>
            <button onClick={handleSendPlan} disabled={sending}>
              {sending ? "Sending..." : "Send Plan"}
            </button>
            {sendStatus && (
              <p
                className={`plan-msg ${sendStatus.includes("fail") || sendStatus.includes("Error") ? "msg-error" : "msg-ok"}`}
              >
                {sendStatus}
              </p>
            )}
          </div>

          {/* Downloads */}
          <div className="plan-section">
            <h3>3. Download your data</h3>
            <p className="text-muted">Download your conversation transcript before closing.</p>
            <div className="download-row">
              <a className="btn-download" href="#" onClick={handleDownloadTranscript}>
                Download Transcript
              </a>
            </div>
          </div>

          {/* Close session */}
          <div className="plan-section">
            <h3>4. Close session</h3>
            <p className="text-muted">
              This deletes your conversation data and audio recording from the server. You can send
              the plan to email first.
            </p>
            <button className="btn-close" onClick={handleCloseSession} disabled={closing}>
              {closing ? "Closing..." : confirmClose ? "Confirm — delete my data" : "Close Session"}
            </button>
            {confirmClose && !closing && (
              <p className="plan-msg msg-warn">Click again to confirm. This cannot be undone.</p>
            )}
          </div>

          {connected && (
            <button
              className="btn-back"
              onClick={() => {
                setMode("conversation");
                setConfirmClose(false);
              }}
            >
              Back to conversation
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="conversation-dashboard">
      <header className="dashboard-header">
        <div className="brand">
          <div className="brand-logo">
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <div className="brand-meta">
            <h1>Advanced Care Planning</h1>
            <span className="session-tag">Live Session</span>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-plan" onClick={() => setMode("plan")}>
            Session Summary & Actions
          </button>
          <button className="btn-end" onClick={onDisconnect}>
            End Conversation
          </button>
        </div>
      </header>

      <div className="dashboard-content">
        {/* Left column: Voice Status & Live Transcript */}
        <div className="dashboard-left">
          <div className="voice-hub-card">
            <div className="status-indicator-bar">
              <span className={`status-dot ${agentSpeaking ? "speaking" : ""}`} />
              {agentSpeaking ? (
                <div className="speaking-indicator">
                  <span className="speaking-label">Assistant is speaking</span>
                  <div className="waveform">
                    <span className="waveform-bar" />
                    <span className="waveform-bar" />
                    <span className="waveform-bar" />
                    <span className="waveform-bar" />
                    <span className="waveform-bar" />
                  </div>
                </div>
              ) : (
                <span className="listening-label">Assistant is listening...</span>
              )}
            </div>

            <div className="transcript-wrapper">
              <TranscriptPanel messages={transcript} agentSpeaking={agentSpeaking} />
            </div>

            <div className="voice-hub-footer">
              <div className="mic-indicator">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                >
                  <rect x="9" y="2" width="6" height="11" rx="3" />
                  <path d="M5 10a7 7 0 0 0 14 0" />
                  <line x1="12" y1="19" x2="12" y2="22" />
                </svg>
                <span>Mic active — speak freely</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right column: Live Preferences Cards */}
        <div className="dashboard-right">
          <div className="preferences-hub-header">
            <h2>Care Plan Preferences</h2>
            <p>Topics populate automatically as they are discussed during the conversation.</p>
          </div>
          <div className="preferences-grid-container">
            <PreferencesView preferences={preferences} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function _fmt(val: unknown): string {
  if (val === null || val === undefined) return "";
  if (typeof val === "boolean") return val ? "Yes" : "No";
  if (Array.isArray(val)) return val.length > 0 ? val.join(", ") : "";
  return String(val);
}

// ---------------------------------------------------------------------------
// ACP Sections View — shows all 6 sections as cards
// ---------------------------------------------------------------------------

function PreferencesView({ preferences }: { preferences: Record<string, unknown> }) {
  const sections: { key: string; label: string; fields: { key: string; label: string }[] }[] = [
    {
      key: "substitute_decision_maker",
      label: "Substitute Decision-Maker",
      fields: [
        { key: "name", label: "Who" },
        { key: "relationship", label: "Relationship" },
      ],
    },
    {
      key: "quality_of_life",
      label: "Quality of Life",
      fields: [
        { key: "values", label: "What matters" },
        { key: "fears", label: "Concerns" },
      ],
    },
    {
      key: "treatment_preferences",
      label: "Treatment Preferences",
      fields: [
        { key: "life_support", label: "Life support" },
        { key: "cpr", label: "CPR" },
        { key: "feeding_tubes", label: "Feeding tubes" },
        { key: "pain_management", label: "Pain management" },
      ],
    },
    {
      key: "personal_beliefs",
      label: "Values & Beliefs",
      fields: [
        { key: "faith_role", label: "Faith/Spirituality" },
        { key: "cultural_values", label: "Cultural values" },
      ],
    },
    {
      key: "specific_scenarios",
      label: "Specific Scenarios",
      fields: [
        { key: "dementia", label: "Dementia" },
        { key: "coma", label: "Coma" },
        { key: "terminal_illness", label: "Terminal illness" },
      ],
    },
    {
      key: "dignity_and_values",
      label: "Dignity & Values",
      fields: [
        { key: "meaning_of_life", label: "What gives life meaning" },
        { key: "dignity_definition", label: "Definition of dignity" },
      ],
    },
  ];

  return (
    <div className="acp-sections-grid">
      {sections.map((section) => {
        const data = preferences[section.key] as Record<string, unknown> | undefined;
        const isDiscussed = data?.discussed === true;
        return (
          <div key={section.key} className={"acp-card " + (isDiscussed ? "discussed" : "pending")}>
            <div className="acp-card-header">
              <span className="acp-card-status">{isDiscussed ? "✓" : "○"}</span>
              <span className="acp-card-title">{section.label}</span>
            </div>
            <div className="acp-card-body">
              {isDiscussed ? (
                section.fields.map((field) => {
                  const raw = data?.[field.key];
                  const val = _fmt(raw);
                  if (!val) return null;
                  return (
                    <div key={field.key} className="acp-field">
                      <span className="acp-field-label">{field.label}</span>
                      <span className="acp-field-value">{val}</span>
                    </div>
                  );
                })
              ) : (
                <p className="acp-pending">Waiting for this topic to come up in conversation...</p>
              )}
              {isDiscussed && data && _fmt(data.notes) && (
                <div className="acp-field">
                  <span className="acp-field-label">Notes</span>
                  <span className="acp-field-value">{_fmt(data.notes)}</span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
