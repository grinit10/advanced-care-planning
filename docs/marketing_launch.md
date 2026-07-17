# 🚀 Marketing Launch & Virality Strategy

To get the **Advanced Care Planning (ACP) Voice AI Assistant** noticed by developers, health-tech professionals, and clinicians, you should execute a coordinated launch across developer communities and health-tech networks.

Here is a ready-to-use launch playbook, social media copy templates, and a technical blog outline.

---

## 1. Target Communities & Platforms

### 💡 Hacker News (Show HN)
- **Why**: Hacker News values open-source projects that address real-world human problems, respect privacy, and use cutting-edge technology.
- **Hook**: Live voice interaction, ephemeral privacy (zero data stored on disk), and standard FHIR data exports.

### 🤖 Reddit
- **r/selfhosted**: Highlight the local Docker deployment, Redis ephemeral storage, and offline capability.
- **r/healthtech**: Focus on the EMR/FHIR integration and how this solves the patient experience problem of documenting wishes.
- **r/LocalLLaMA**: Discuss the architecture of combining LiveKit, Deepgram, and Groq for ultra-low latency.

### 💼 LinkedIn
- **Why**: Perfect for reaching clinical administrators, doctors, social workers, and palliative care specialists.
- **Hook**: Gentle patient-led AI voice assistants, clinical integrations, and reducing clinician administrative overhead.

---

## 2. Ready-to-Use Copy Templates

### 📝 Hacker News (Show HN)

**Title**: `Show HN: Ephemeral Palliative Voice AI with EMR/FHIR Integrations`

**Show HN Description**:
```text
Hey HN,

We built an open-source voice AI assistant designed to guide patients through the emotionally difficult process of Advanced Care Planning (documenting future healthcare wishes, substitute decision-makers, and life support preferences).

Planning for end-of-life care is critical, yet current paper-based forms are clinical and intimidating. Our system uses a low-latency voice interface to make this a supportive conversation.

Key Architecture & Design:
1. Real-time Voice: LiveKit WebRTC + Deepgram (STT/TTS Aura-2) + Groq (Llama-3.1-8B-instant) in Sydney data-centers for low-latency voice loops.
2. Background Extractor: Azure OpenAI (gpt-4o-mini) extracts preferences (substitute decision-makers, values, treatment thresholds) asynchronously in the background.
3. Ephemeral Privacy by Design: All patient inputs, transcripts, and preferences are stored strictly in volatile memory (Redis). Once the browser session is closed, all data is completely deleted.
4. EMR Integration: Exports a standard HL7/FHIR QuestionnaireResponse JSON so hospitals can directly ingest the care wishes into Epic or Cerner.

Check out the code here: https://github.com/your-username/advanced-care-planning

Would love your feedback on the architecture, latency, and how we handle local container deployments for clinical environments.
```

---

### 💬 Reddit (r/selfhosted & r/healthtech)

**Title**: `Self-Hosted Ephemeral Voice AI for Palliative Care Planning (with FHIR Export)`

**Body**:
```text
Hi everyone,

I wanted to share a self-hosted health-tech project we've been working on: **Advanced Care Planning Voice Assistant**.

It runs entirely inside Docker and is designed to sit on a clinician’s tablet. A facilitator hands it to a patient, and they have a comfortable voice conversation about their values, substitute decision-makers, and treatment wishes.

Why self-hosted & ephemeral?
Health data is highly sensitive. The solution runs a local LiveKit Server, Redis, and Python Voice Agent. All data is stored strictly in Redis RAM. Once the patient hits "Close Session", the Redis key is deleted and all audio files are wiped from the host.

Features:
- Dynamic Canvas Wave Visualizer (pulses when listening, active wave when speaking).
- Real-time checklist tracking which topics have been discussed.
- One-click docx download or standard FHIR QuestionnaireResponse JSON export for EMR ingestion.

Setup takes ~15 minutes:
1. Clone the repo: git clone https://github.com/your-username/advanced-care-planning
2. Fill in the API keys in `.env` (Groq, Deepgram, Azure OpenAI).
3. Run `./scripts/setup.sh` (or `.\scripts\setup.ps1` on Windows). The script dynamically detects your IP and checks/resolves port conflicts automatically!

GitHub Repo: https://github.com/your-username/advanced-care-planning

Looking forward to hearing your thoughts, especially around self-hosted privacy standards in clinical workflows!
```

---

### 💼 LinkedIn (Palliative Care & Health-Tech)

**Post Copy**:
```text
Advanced Care Planning (ACP) is one of the most critical aspects of palliative care, yet many patients find paper-based questionnaires clinical, cold, or emotionally overwhelming.

We built an open-source Voice AI Assistant to solve this. 🏥

Designed for on-site clinical tablets, this assistant uses a supportive, empathetic voice to guide patients through discussing their future healthcare wishes, substitute decision-makers, and quality of life values. 

Key Features for Clinicians:
✅ Calming Voice Interface: Ultra-low latency voice loops powered by LiveKit, Groq, and Deepgram.
✅ EMR Ready: Exports structured plans directly as HL7/FHIR QuestionnaireResponse JSON payloads for systems like Epic and Cerner.
✅ Ephemeral Privacy: Operates strictly in-memory (volatile Redis). No local data is persisted to disk, and everything is deleted once the session closes.
✅ Interactive Progress: Patients see topics light up as they are addressed, ensuring a structured yet conversational flow.

Special thanks to LiveKit for the WebRTC infrastructure.

Open-source under MIT: https://github.com/your-username/advanced-care-planning

#HealthTech #PalliativeCare #FHIR #GenerativeAI #HealthcareAI #DigitalHealth
```

---

## 3. Technical Blog Post Outline

### Title: How We Built an Ephemeral, Low-Latency Palliative Voice AI Assistant

#### **1. Introduction**
- The human problem: Why Advanced Care Planning is vital but current processes fail.
- The solution: A voice agent that listens, summarizes, and disappears.

#### **2. Architecture Overview**
- Explain the pipeline: WebRTC (LiveKit) → VAD (Silero) → STT (Deepgram Nova-3) → Voice LLM (Groq Llama-3.1) → TTS (Deepgram Aura-2) → WebRTC.
- Detail the background processing: Why we separate the conversational loop (Groq LPU) from the extraction loop (Azure OpenAI `gpt-4o-mini`).

#### **3. Privacy by Design: Ephemeral Storage**
- Explaining the data flow.
- How Redis manages volatile states.
- The cleanup mechanism on `/close` session that deletes memory keys and deletes local audio recording.

#### **4. Integration with EMRs (FHIR standard)**
- Why PDF summaries are not enough for modern hospitals.
- Mapping Python dicts to a standard FHIR `QuestionnaireResponse` resource.
- code snippet of `to_fhir_questionnaire_response`.

#### **5. Overcoming Developer Friction**
- Automatic LAN IP detection.
- Port-clash handling in shell/powershell scripts.

#### **6. Conclusion & Open Source Call to Action**
- Invitation for developers to contribute templates for different countries/states.
