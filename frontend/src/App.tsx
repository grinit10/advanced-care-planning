import { useState, useCallback, useEffect } from "react";
import PreJoin from "./components/PreJoin";
import ConversationView from "./components/ConversationView";
import { useVoiceAgent } from "./hooks/useVoiceAgent";

type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  const stored = localStorage.getItem("acp-theme");
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [error, setError] = useState<string | null>(null);

  const {
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
  } = useVoiceAgent();

  // Apply theme to <html> and persist to localStorage
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("acp-theme", theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((t) => (t === "light" ? "dark" : "light"));
  }, []);

  const handleJoin = useCallback(
    async (roomName: string, identity: string) => {
      setError(null);
      try {
        await connect(roomName, identity);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        setError(message);
      }
    },
    [connect]
  );

  const handleDisconnect = useCallback(() => {
    disconnect();
  }, [disconnect]);

  const handleRegisterEmail = useCallback(
    async (email: string) => {
      return await registerEmail(email);
    },
    [registerEmail]
  );

  const handleSendPlan = useCallback(async () => {
    return await sendPlan();
  }, [sendPlan]);

  const handleCloseSession = useCallback(async () => {
    return await closeSession();
  }, [closeSession]);

  if (error) {
    return (
      <div className="app">
        <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === "light" ? "🌙" : "☀️"}
        </button>
        <div className="error-view">
          <h2>Connection Error</h2>
          <p>{error}</p>
          <p className="text-muted">
            Make sure Docker Compose is running (
            <code>docker compose up -d</code>) and your .env file has the correct
            Azure OpenAI credentials.
          </p>
          <button onClick={() => setError(null)}>Try Again</button>
        </div>
      </div>
    );
  }

  if (!connected) {
    return (
      <div className="app">
        <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === "light" ? "🌙" : "☀️"}
        </button>
        <PreJoin onJoin={handleJoin} connecting={connecting} />
      </div>
    );
  }

  return (
    <div className="app">
      <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle theme">
        {theme === "light" ? "🌙" : "☀️"}
      </button>
      <ConversationView
        transcript={transcript}
        agentSpeaking={agentSpeaking}
        preferences={preferences}
        roomId={roomId}
        onRegisterEmail={handleRegisterEmail}
        onSendPlan={handleSendPlan}
        onCloseSession={handleCloseSession}
        onDisconnect={handleDisconnect}
      />
    </div>
  );
}