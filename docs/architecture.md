# 🏗 Architecture & Data Flow

This document details the underlying system architecture, components, data flows, and data residency policies of the Advanced Care Planning (ACP) voice assistant.

## System Diagram

```
┌──────────────┐     WebRTC     ┌────────────────────┐     Deepgram API      ┌──────────────┐
│   Frontend   │◄──────────────►│  LiveKit Server    │◄─────────────────────►│   Deepgram   │
│  (React/TS)  │                │   (Docker Local)   │  (api.au.deepgram.com)│  STT + TTS   │
│              │                │                    │  AWS Sydney           │  (Nova-3,    │
│              │                │                    │  ap-southeast-2       │  Aura-2)     │
└──────────────┘                └────────┬───────────┘                       └──────────────┘
                                         │
                                         │ Agent Dispatch (Redis)              Groq LPU (Sydney)
                                         │                                   ┌──────────────┐
                                 ┌───────▼────────┐                          │     Groq     │
                                 │  Voice Agent   │◄────────────────────────►│  (Voice LLM) │
                                 │   (Python)     │  Groq API                │  llama-3.1   │
                                 │ VAD→STT→LLM→TTS│                          └──────────────┘
                                 └───────┬────────┘                            Azure OpenAI
                                         │                                   ┌──────────────┐
                                         │ Extracted Preferences             │    Azure     │
                                         └──────────────────────────────────►│    OpenAI     │
                                                                             │ (Extractor)  │
                                                                             └──────────────┘
```

---

## Component Breakdown

| Component | Role | Technology |
|-----------|------|------------|
| **Frontend** | Web UI with microphone access, real-time transcription, and plan download options. | React + TypeScript + Vite |
| **LiveKit Server** | Manages high-performance WebRTC media routing. | Go (LiveKit) |
| **Redis** | Agent dispatch queue and local ephemeral session memory storage. | Redis 7 |
| **Voice Agent** | Python-based worker managing the pipeline: VAD → STT → LLM → TTS. | Python (LiveKit Agents) |
| **Token Server** | Exposes an endpoint to generate secure JWT tokens for LiveKit authentication. | Python (aiohttp) |
| **Groq** | Orchestrates the primary conversation voice model with ultra-low latency. | Cloud API (Sydney LPU cluster) |
| **Azure OpenAI** | Handles background preference extraction and final `.docx` summary compilation. | Cloud API (Australia East) |
| **Deepgram** | Fast speech-to-text (STT) and text-to-speech (TTS) conversion. | Cloud API (AWS Sydney) |

---

## Detailed Data Flow (One Conversation Turn)

1. **Audio Capture**: The patient speaks into their microphone. The frontend captures raw audio and transmits it over **WebRTC** to the local **LiveKit Server**.
2. **Speech Boundaries**: The **Voice Agent** subscribes to the WebRTC audio track. It uses **Silero VAD** locally to identify the start and end of patient speech.
3. **Speech to Text**: The agent sends the audio segment to the **Deepgram STT** Australian endpoint (`api.au.deepgram.com`) to generate a text transcription.
4. **Empathetic Response Generation**: The transcribed text is sent to the **Groq API** with the ACP guidelines and prompt. Groq returns a text response.
5. **Speech Synthesis**: The response text is streamed to the **Deepgram TTS** Australian endpoint to synthesize a natural-sounding audio stream.
6. **WebRTC Playback**: The synthesized audio is streamed back through LiveKit Server to the user's browser, allowing immediate, interrupted-capable playback.
7. **Preference Extraction**: Concurrently, the transcript is analyzed by **Azure OpenAI** to extract structured clinical preferences (values, substitute decision-maker names, and treatment thresholds) without blocking the conversation flow.

---

## Data Residency & Security

Privacy and data location are paramount for healthcare applications.

* **Local Sandbox**: The LiveKit media router, Redis database, Token Server, and Python Voice Agent run entirely inside your local machine or private container environment. 
* **Real-time Audio Processing**: Audio sent to **Deepgram** is processed in-memory at their Sydney data center (`ap-southeast-2`) and is immediately discarded. No audio recordings are trained on or stored.
* **Real-time Text Processing**: Prompts sent to **Groq** and **Azure OpenAI** are handled under a Zero Data Retention (ZDR) policy. No inputs are logged or persisted.
* **Ephemeral In-Memory Database**: Patient state, preferences, and transcripts are stored purely in-memory inside Redis. Once the browser session is closed, or the local environment is restarted, all database content is completely wiped.
