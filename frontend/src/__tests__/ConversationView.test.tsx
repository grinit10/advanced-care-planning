import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ConversationView from "../components/ConversationView";

describe("ConversationView", () => {
  const defaultProps = {
    transcript: [],
    agentSpeaking: false,
    preferences: {},
    planSummary: "",
    roomId: "test-room",
    onRegisterEmail: vi.fn(),
    onSendPlan: vi.fn(),
    onCloseSession: vi.fn(),
    onDisconnect: vi.fn(),
    connected: false,
  };

  beforeEach(() => {
    vi.restoreAllMocks();
    window.open = vi.fn();
  });

  it("calls window.open with correct transcript URL when clicking download transcript", async () => {
    render(<ConversationView {...defaultProps} />);

    const downloadLink = screen.getByText("Download Transcript");
    expect(downloadLink).toBeInTheDocument();

    // Trigger click
    fireEvent.click(downloadLink);

    expect(window.open).toHaveBeenCalledWith(
      "http://localhost:8082/transcript/test-room",
      "_blank",
    );
  });

  it("calls window.open with correct plan docx URL when clicking download plan", async () => {
    render(<ConversationView {...defaultProps} />);

    const downloadLink = screen.getByText("Download Plan (.docx)");
    expect(downloadLink).toBeInTheDocument();

    // Trigger click
    fireEvent.click(downloadLink);

    expect(window.open).toHaveBeenCalledWith(
      "http://localhost:8082/plan-docx/test-room",
      "_blank",
    );
  });
});
