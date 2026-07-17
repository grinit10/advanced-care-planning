# 🏥 Advanced Care Planning (ACP) — Voice AI Assistant

> **A compassionate, conversational voice assistant that helps people think through and document their future healthcare wishes.**

---

### 💡 What is Advanced Care Planning (ACP)?
Imagine a situation where you become seriously ill or injured, and you cannot speak or make decisions for yourself. Who will speak for you? What kind of medical treatments would you want—or not want?
* **Advanced Care Planning (ACP)** is the process of thinking about, discussing, and planning for your future health and personal care.
* It ensures your values, beliefs, and treatment preferences are known so they can guide your family and healthcare team if you cannot communicate.

[![What is Advanced Care Planning?](https://img.youtube.com/vi/ClvlOLQUl34/maxresdefault.jpg)](https://youtu.be/ClvlOLQUl34)
*Watch this short introduction video explaining the importance and process of Advanced Care Planning.*

### 🎯 Purpose of This Solution
Documenting future wishes can feel intimidating, clinical, or emotionally overwhelming. This solution provides a **friendly, natural voice assistant** that:
1. **Guides the Conversation**: Gently walks a patient through key topics (substitute decision-makers, treatment preferences, quality of life thresholds, and faith/cultural values) in a conversational, non-threatening way.
2. **Generates an Actionable Plan**: Dynamically extracts preferences in the background to build a structured summary and downloadable Word document (`.docx`) of wishes.
3. **Clinical EMR Integration (FHIR)**: Supports exporting structured plans directly to the **HL7/FHIR `QuestionnaireResponse`** format, enabling hospitals to ingest patient wishes directly into EMR systems like Epic or Cerner.
4. **Calming Audio Visualizer & Progress Tracker**: Features a premium canvas-based sinusoidal visualizer and a real-time progress tracker showing how many ACP topics have been successfully discussed.
5. **Zero-Friction Network Setup**: Auto-detects network LAN IPs and dynamically resolves local port conflicts (e.g. if port `5173` is busy) on startup.
6. **Protects Patient Dignity & Privacy**: Designed specifically for clinical tablets on-site, ensuring zero data is persisted locally and all information is vaporized once the session ends.

---

> [!IMPORTANT]
> **Facilitated & Ephemeral Privacy by Design**
> * **Clinician-Led/Facilitated Sessions**: The assistant is designed to be opened and configured by a healthcare practitioner, social worker, or family member (the facilitator) who then hands the device to the user.
> * **Strict Ephemerality**: All patient preferences and session transcripts are stored strictly in-memory (volatile Redis). No patient data is ever persisted to disk. When the container reboots or a new session starts, the previous user's sensitive data is completely vaporized.
> * **Retrieval & Sharing Window**: Session summaries, emails, or reports can *only* be shared or retrieved while the active browser session is open. Once the tab is closed, refreshed, or the containers are stopped, the data is permanently destroyed.

---

## 📖 Table of Contents

- [🚀 Quick Start (~30-45 minutes)](#-quick-start-30-45-minutes)
- [🏗 Architecture & Data Flow](docs/architecture.md)
- [⚙️ Configuration Reference](docs/configuration.md)
- [🚀 Deployment Guide](docs/deployment.md)
- [🛠 Development Guide](docs/development.md)
- [🇦🇺 Australian ACP Context & Resources](docs/australian_acp.md)
- [🔍 Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start (~30-45 minutes)

### What You'll Need

| Requirement | Where to Get It |
|------------|-----------------|
| **Docker Desktop** (free) | https://www.docker.com/products/docker-desktop/ |
| **Azure account** (free) | https://portal.azure.com (get $200 AUD free credits) |
| **Deepgram account** (free) | https://console.deepgram.com (includes 200 free minutes/month) |
| **Groq account** (free) | https://console.groq.com |
| **A microphone** | Built into most laptops |

**That's it. No Python. No Node.js. No coding.**

---

### Step 1: Install Docker Desktop

1. Go to https://www.docker.com/products/docker-desktop/
2. Click the **"Download for Windows"** button (or Mac/Linux)
3. Open the downloaded file and follow the installation wizard.
4. After installation, open **Docker Desktop** from your Start menu and wait until you see **"Engine running"** in the bottom-left corner.

---

### Step 2: Set Up Azure OpenAI

You need an Azure OpenAI resource with 1 model deployed. Follow these steps:

#### 2a. Create an Azure OpenAI Resource
1. Go to https://portal.azure.com and sign in.
2. In the top search bar, type **"Azure OpenAI"** and select it.
3. Click **"+ Create"** → **"Azure OpenAI"** and fill in the form:
   - **Resource group**: Click **"Create new"** → type **`acp-rg`**
   - **Region**: Select **"Australia East"** (Sydney — lowest latency for Australian users)
   - **Name**: Type **`acp-openai`**
   - **Pricing tier**: **Standard S0**
4. Click **"Next"** → **"Next"** → **"Create"**.
5. Wait for deployment to finish → click **"Go to resource"**.

#### 2b. Deploy Models
1. In your OpenAI resource page, click **"Explore"** (or **"Go to Azure AI Foundry"**).
2. Click **"Deployments"** on the left.
3. Click **"Create new deployment"** and deploy:
   * **gpt-4o-mini** (Deployment Name: `gpt-4.1-mini-aus`)
4. Click **"Create"**.

#### 2c. Copy Your Keys
1. Go back to the Azure portal tab.
2. On the left menu, click **"Keys and Endpoint"**.
3. Copy **Key 1** and the **Endpoint** URL (e.g. `https://acp-openai.openai.azure.com`).

---

### Step 2d: Set Up Deepgram for STT and TTS
Speech-to-text and text-to-speech are handled by **Deepgram** via their Australian endpoint (`api.au.deepgram.com`) running in AWS Sydney.

1. Go to https://console.deepgram.com and sign up.
2. Go to **"API Keys"** in the left menu.
3. Click **"Create a new API Key"**, give it a name (e.g. `acp-agent`), and copy the key.

---

### Step 2e: Set Up Groq for Low-Latency Voice
The live voice conversation uses **Groq** for LPU inference, hosted in Sydney for low latency.

1. Go to https://console.groq.com and sign up.
2. Go to **"API Keys"** in the left menu.
3. Click **"Create API Key"**, copy it, and keep it safe.

---

### Step 3: Download and Configure the Project

```bash
git clone https://github.com/YOUR-REPO/advanced-care-planning.git
cd advanced-care-planning
```

#### Create the .env File
1. In the project folder, make a copy of **`.env.example`** and rename it to **`.env`**.
2. Open the `.env` file in **Notepad** (or any editor).
3. The `.env` template looks like this:
   ```ini
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
   AZURE_OPENAI_API_KEY=your-api-key-here
   AZURE_OPENAI_API_VERSION=2024-10-01-preview
   AZURE_OPENAI_EXTRACTOR_LLM_DEPLOYMENT=gpt-4o-mini
   GROQ_API_KEY=your-groq-api-key-here
   GROQ_VOICE_MODEL=llama-3.1-8b-instant
   DEEPGRAM_API_KEY=your-deepgram-api-key-here
   LIVEKIT_API_KEY=devkey
   LIVEKIT_API_SECRET=devsecret
   ACS_SENDER_DOMAIN=DoNotReply@abc123.azurecomm.net
   ```
4. Replace the placeholders with your actual keys and endpoints:
   - `AZURE_OPENAI_ENDPOINT` -> Your Azure Endpoint URL
   - `AZURE_OPENAI_API_KEY` -> Your Azure Key 1
   - `GROQ_API_KEY` -> Your Groq API Key
   - `DEEPGRAM_API_KEY` -> Your Deepgram API Key
5. **Save the file** and close it.

---

### Step 4: Start Everything

#### Windows (Easy Way)
Double-click the **`scripts/setup.ps1`** file. Or open a terminal:
```powershell
docker compose up -d
```

#### Mac / Linux (Easy Way)
Run the setup script:
```bash
bash scripts/setup.sh
```

---

### Step 5: Talk to the AI

1. Open your web browser.
2. Go to **http://localhost:5173**.
3. Type your name in the box.
4. Click **"Start Conversation"** and allow microphone access.
5. **Start speaking!** The AI will guide you through your care planning.

[![How to Use the UI](https://img.youtube.com/vi/QMd7MrDQtds/maxresdefault.jpg)](https://youtu.be/QMd7MrDQtds)
*Watch this tutorial video to see how to use the UI and interact with the Voice AI Assistant.*

---

### Step 6: When You're Done

To stop everything:
```bash
docker compose down
```

---

## 🔍 Troubleshooting

### "Docker Engine is not running"
* Open **Docker Desktop** from your Start menu and wait for the green "Engine running" indicator.

### "Connection Error" in the browser
* Make sure all services are running: `docker compose ps`
* Check the agent logs: `docker compose logs agent`
* Verify your `.env` file has the correct Azure OpenAI credentials.

### No audio / Can't hear the AI
* Check your browser's microphone permission (look for a mic icon in the address bar).
* Make sure your speakers are on and not muted.

---

## 📄 License
MIT

---

## 🙏 Acknowledgments
* [LiveKit](https://livekit.io) — Open-source WebRTC platform
* [Azure OpenAI](https://azure.microsoft.com/products/ai-services/openai-service) — LLM hosted in Australia East
* [Deepgram](https://deepgram.com) — STT and TTS via Australian endpoint
* [Advance Care Planning Australia](https://www.advancecareplanning.org.au) — National ACP advisory body