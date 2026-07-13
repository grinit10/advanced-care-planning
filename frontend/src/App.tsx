import { useState, useCallback } from "react";
import PreJoin from "./components/PreJoin";
import ConversationView from "./components/ConversationView";
import { useVoiceAgent } from "./hooks/useVoiceAgent";

export default function App() {
  const {
    connecting,
    connected,
    transcript,
    connect,
    disconnect,
    registerEmail,
    sendPlan,
    closeSession,
  } = useVoiceAgent();
  const [error, setError] = useState<string | null>(null);

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
        <PreJoin onJoin={handleJoin} connecting={connecting} />
      </div>
    );
  }

  return (
    <div className="app">
      <ConversationView
        transcript={transcript}
        onRegisterEmail={handleRegisterEmail}
        onSendPlan={handleSendPlan}
        onCloseSession={handleCloseSession}
        onDisconnect={handleDisconnect}
      />
    </div>
  );
}