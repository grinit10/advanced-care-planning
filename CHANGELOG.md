# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-07-13

### Added

- **Voice AI Agent:** Full conversation pipeline with VAD (Silero), STT (Deepgram
  Nova-3 via Australian endpoint), LLM (Azure OpenAI GPT-4.1-mini in Australia East),
  and TTS (Deepgram Aura-2 via Australian endpoint).
- **Web UI:** React + TypeScript frontend with live transcript, real-time preference
  extraction display, and session management.
- **LiveKit Integration:** WebRTC-based real-time audio streaming with local
  LiveKit server for media routing.
- **Session Management:** Redis-backed session store with transcript persistence,
  structured preference extraction, and audio recording.
- **Plan Delivery:** Email-based ACP plan delivery via Azure Communication Services,
  with optional WAV audio recording attachment.
- **Docker Compose Deployment:** Single-command local setup with all services
  (Redis, LiveKit, agent, token server, frontend).
- **Helm Chart:** Kubernetes deployment with configurable scaling, secrets, and
  ingress support.
- **Australian ACP Focus:** Conversation guide tailored to Australian healthcare
  context, state-specific resources, and data residency in Australia (Azure
  Australia East + Deepgram AWS Sydney).
- **Setup Scripts:** Auto-detection of host LAN IP for LiveKit WebRTC ICE
  configuration on Windows (PowerShell) and Linux/macOS (Bash).

### Security

- Sensible local development defaults with `.gitignore` excluding `.env` files.
- All voice data processed in real-time and discarded — no persistent storage
  of audio beyond the optional WAV recording.