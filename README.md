# 🏥 Advanced Care Planning — Voice AI Assistant

> **Have a conversation with AI about your future healthcare wishes.**
> Everything runs on your computer — your voice data never leaves your home.
> Designed with the Australian healthcare context in mind.

---

## 📋 Table of Contents

- [Quick Start (10 minutes)](#-quick-start-10-minutes)
- [How It Works](#-how-it-works)
- [Australian ACP Context](#-australian-acp-context)
- [Option A: Local with Docker Compose (Recommended)](#option-a-local-with-docker-compose)
- [Option B: Kubernetes with Helm](#option-b-kubernetes-with-helm)
- [Architecture](#-architecture)
- [Configuration Reference](#-configuration-reference)
- [Development Guide](#-development-guide)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start (10 minutes)

### What You'll Need

| Requirement | Where to Get It |
|------------|-----------------|
| **Docker Desktop** (free) | https://www.docker.com/products/docker-desktop/ |
| **Azure account** (free) | https://portal.azure.com (get $200 AUD free credits) |
| **A microphone** | Built into most laptops |

**That's it. No Python. No Node.js. No coding.**

---

### Step 1: Install Docker Desktop

1. Go to https://www.docker.com/products/docker-desktop/
2. Click the **"Download for Windows"** button (or Mac/Linux)
3. Open the downloaded file and follow the installation wizard
4. After installation, open **Docker Desktop** from your Start menu
5. Wait until you see **"Engine running"** in the bottom-left corner

> ⏳ This might take a few minutes the first time. Docker Desktop needs to start its virtual machine.

---

### Step 2: Set Up Azure OpenAI

You need an Azure OpenAI resource with 3 models deployed. Follow these steps:

#### 2a. Create an Azure OpenAI Resource

1. Go to https://portal.azure.com and sign in
2. In the top search bar, type **"Azure OpenAI"** and select it
3. Click **"+ Create"** → **"Azure OpenAI"**
4. Fill in the form:
   - **Subscription**: Select your subscription
   - **Resource group**: Click **"Create new"** → type **`acp-rg`**
   - **Region**: Select **"Australia East"** (Sydney — lowest latency for Australian users, and all required models are available)
   - **Name**: Type **`acp-openai`**
   - **Pricing tier**: **Standard S0**
5. Click **"Next"** → **"Next"** → **"Create"**
6. Wait for deployment to finish (1-2 minutes) → click **"Go to resource"**

#### 2b. Deploy Models

1. In your OpenAI resource page, click **"Explore"** (or **"Go to Azure AI Foundry"**)
2. Azure AI Foundry opens in a new tab. Click **"Deployments"** on the left
3. Click **"Create new deployment"** and deploy these 3 models one at a time:

   | Model | Deployment Name | Purpose |
   |-------|----------------|---------|
   | **gpt-4.1-mini-aus** | `gpt-4.1-mini-aus` | The brain (conversation) |

   > **STT & TTS are handled by Deepgram (not Azure OpenAI).**
   > See [Step 2d](#setup-deepgram-for-stt-and-tts) below.

   For each model:
   - Select the model from the dropdown
   - Type the **Deployment Name** exactly as shown above
   - Click **"Create"**

#### 2c. Copy Your Keys

1. Go back to the Azure portal tab (not AI Foundry)
2. You should still be in your `acp-openai` resource page
3. On the left menu, click **"Keys and Endpoint"**
4. Copy **Key 1** (click the copy icon)
5. Copy the **Endpoint** URL (looks like `https://acp-openai.openai.azure.com`)

> 💡 **Australia East tip:** Hosting your OpenAI resource in Sydney means lower latency for Australian users. Your data is processed in Australia and stays within Australian borders for the AI processing step.

---

### Step 2d: Set Up Deepgram for STT and TTS

Speech-to-text and text-to-speech are handled by **Deepgram**, not Azure OpenAI. Deepgram has an Australian endpoint (`api.au.deepgram.com`) running on AWS Sydney — your voice data stays in Australia.

1. Go to https://console.deepgram.com and sign up (free tier includes 200 minutes/month)
2. Go to **"API Keys"** in the left menu
3. Click **"Create a new API Key"**, give it a name (e.g. `acp-agent`), and copy the key
4. You'll add this key to your `.env` file in the next step

### Step 3: Download and Configure the Project

#### Option A: Download ZIP
1. Go to the GitHub repository page
2. Click **"Code"** → **"Download ZIP"**
3. Extract the ZIP file to a folder on your computer

#### Option B: Git Clone
```bash
git clone https://github.com/YOUR-REPO/advanced-care-planning.git
cd advanced-care-planning
```

#### Create the .env File

1. In the project folder, you'll see a file named **`.env.example`**
2. Make a copy of it and rename the copy to **`.env`** (remove the `.example` part)
3. Open the `.env` file in **Notepad** (right-click → Open with → Notepad)
4. It should look like this:

```ini
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-10-01-preview
AZURE_OPENAI_LLM_DEPLOYMENT=gpt-4.1-mini-aus
DEEPGRAM_API_KEY=your-deepgram-api-key-here
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=devsecret
```

5. Replace these values with what you copied in Step 2c:
   - Replace `https://your-resource-name.openai.azure.com` with your **Endpoint**
   - Replace `your-api-key-here` with your **Key 1**
6. **Save the file** (Ctrl+S) and close Notepad

---

### Step 4: Start Everything

#### Windows (Easy Way)
Double-click the **`scripts/setup.ps1`** file. Or open a terminal:

```powershell
cd C:\Path\To\advanced-care-planning
docker compose up -d
```

#### Mac / Linux (Easy Way)
Run the setup script:
```bash
cd /path/to/advanced-care-planning
bash scripts/setup.sh
```

Or directly with Docker Compose:
```bash
docker compose up -d
```

> ⏳ **First time only:** This downloads and builds all the Docker images. It may take 3-5 minutes.
> Subsequent starts will be instant.

#### Check That Everything Is Running

```bash
docker compose ps
```

You should see all 5 services with status "Up":

| Service | Status |
|---------|--------|
| redis | Up |
| livekit-server | Up |
| token-server | Up |
| agent | Up |
| frontend | Up |

---

### Step 5: Talk to the AI

1. Open your web browser
2. Go to **http://localhost:5173**
3. Type your name in the box
4. Click **"Start Conversation"**
5. When your browser asks for microphone permission, click **"Allow"**
6. **Start speaking!** The AI will guide you through your care planning

> 💡 **Tips:**
> - Speak clearly at a normal pace
> - Wait for the AI to finish responding before speaking
> - You can interrupt the AI at any time
> - Your conversation transcript is displayed on screen

---

### Step 6: When You're Done

To stop everything:

```bash
docker compose down
```

To restart later:

```bash
docker compose up -d
```

---

## 🤔 How It Works

1. You speak into your browser's microphone
2. Audio is sent to the **LiveKit server** (running on your computer)
3. The **Voice Agent** receives the audio:
   - **VAD** (Voice Activity Detection) finds where your speech starts and ends
   - **Deepgram STT** (Nova-3, via `api.au.deepgram.com`) converts your speech to text
   - **Azure OpenAI LLM** generates a thoughtful response about ACP
   - **Deepgram TTS** (Aura, via `api.au.deepgram.com`) converts the response text to natural-sounding speech
4. You hear the AI's response through your speakers
5. The conversation transcript appears on the screen

**Your voice data goes: Browser → LiveKit → Azure OpenAI → LiveKit → Browser**
**Everything stays on your local network. No data is stored.**

---

## 🇦🇺 Australian ACP Context

### Why This Matters in Australia

Advanced Care Planning helps you document your preferences for future healthcare — so your voice is heard even if you can't speak for yourself. In Australia:

- **1 in 3 Australians** over 65 will need someone else to make healthcare decisions for them
- **Each state and territory** has its own ACP laws and forms (NSW, VIC, QLD, WA, SA, TAS, ACT, NT)
- An **Advance Care Directive** is the legal document that records your wishes
- A **Substitute Decision-Maker** (also called Medical Enduring Power of Attorney in some states) is the person you appoint to make decisions on your behalf
- Your GP, specialist, or local hospital can help you formalise your directive

### What This AI Covers

The conversation guides you through:
- Choosing a **Substitute Decision-Maker** (who you trust to speak for you)
- Documenting your **values and beliefs** about healthcare
- Specifying your preferences for **life-sustaining treatment**
- Outlining your **quality of life** thresholds
- Providing guidance for **end-of-life care** that aligns with your values

> ⚠️ **Important:** This tool helps you *think through and articulate* your preferences. It does **not** create legally binding documents. After your conversation, we recommend formalising your wishes with an official Advance Care Directive through your state or territory's health department. You can find state-specific forms at [advancecareplanning.org.au](https://www.advancecareplanning.org.au).

### State and Territory Resources

| State/Territory | ACP Programme | Website |
|----------------|---------------|---------|
| **NSW** | NSW Advance Care Planning | https://www.health.nsw.gov.au/acp |
| **VIC** | Advance Care Planning Victoria | https://www.advancecareplanning.org.au/victoria |
| **QLD** | Advance Care Planning Queensland | https://www.advancecareplanning.org.au/queensland |
| **WA** | WA Advance Care Planning | https://www.advancecareplanning.org.au/western-australia |
| **SA** | SA Advance Care Planning | https://www.advancecareplanning.org.au/south-australia |
| **TAS** | Tasmanian ACP | https://www.advancecareplanning.org.au/tasmania |
| **ACT** | ACT ACP | https://www.advancecareplanning.org.au/act |
| **NT** | NT ACP | https://www.advancecareplanning.org.au/northern-territory |

### Key Australian Healthcare Terms

| Term | Meaning |
|------|---------|
| **Advance Care Directive** | Legal document recording your healthcare wishes |
| **Substitute Decision-Maker** | Person appointed to make decisions for you |
| **Medical Enduring Power of Attorney** | Legal appointment of a decision-maker (used in some states) |
| **Enduring Guardian** | Appointed to make health and lifestyle decisions (NSW, TAS) |
| **Life-sustaining treatment** | Medical treatments that keep you alive (ventilator, CPR, etc.) |
| **Palliative care** | Comfort-focused care for people with life-limiting illness |
| **My Aged Care** | Australian Government portal for aged care services |
| **Advance Care Planning Australia** | National ACP advisory body |

---

## Option A: Local with Docker Compose

This is the recommended way to run the project. It starts all components with a single command.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Azure OpenAI](https://portal.azure.com) resource in **Australia East** with an LLM model deployed (e.g. gpt-4o-mini)
- A [Deepgram](https://console.deepgram.com) API key (Australian endpoint — data stays in Sydney)
- A microphone

### Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR-REPO/advanced-care-planning.git
cd advanced-care-planning

# 2. Create .env file (copy .env.example and fill in your Azure credentials)
cp .env.example .env
# Edit .env with your Azure OpenAI endpoint and key

# 3. Start everything
docker compose up -d

# 4. Open the app
open http://localhost:5173
```

### Useful Commands

```bash
# View all logs
docker compose logs -f

# View agent logs only
docker compose logs -f agent

# Rebuild agent after code changes
docker compose build agent
docker compose up -d

# Stop everything
docker compose down

# Stop and delete all data (clean slate)
docker compose down -v
```

### Project Structure

```
advanced-care-planning/
├── docker-compose.yml        # 🐳 All services in one file
├── livekit.yaml              # LiveKit server configuration
├── .env                      # 🔑 Your Azure credentials (never commit this!)
├── .env.example              # Template for .env
├── agent/                    # 🧠 Python voice agent
│   ├── main.py               # Entry point — connects to LiveKit
│   ├── acp_agent.py          # VoicePipelineAgent (STT → LLM → TTS)
│   ├── acp_prompts.py        # Loads prompt from prompt.yaml
│   ├── prompt_loader.py      # 🔒 Appends locked TTS formatting rules
│   ├── prompt.yaml           # ✏️ EDIT THIS — customise the conversation
│   └── Dockerfile            # Container build
├── frontend/                 # 🌐 Web user interface
│   ├── src/components/       # React UI components
│   ├── src/hooks/            # LiveKit connection hook
│   └── Dockerfile            # Multi-stage build (Node → Nginx)
├── token-server/             # 🔑 Generates LiveKit tokens
│   └── main.py
├── helm/                     # ☸️ Kubernetes Helm chart
└── scripts/
    └── setup.ps1             # ⚡ One-click Windows setup
```

---

## Option B: Kubernetes with Helm

For production or cloud deployments.

### Prerequisites

- A Kubernetes cluster (minikube, kind, AKS, EKS, GKE)
- Helm 3 installed
- Container images built and pushed to a registry

### Build and Push Images

```bash
# Build images
docker build -t myregistry/acp-agent:latest ./agent
docker build -t myregistry/acp-token-server:latest ./token-server
docker build -t myregistry/acp-frontend:latest ./frontend

# Push to registry
docker push myregistry/acp-agent:latest
docker push myregistry/acp-token-server:latest
docker push myregistry/acp-frontend:latest
```

### Install with Helm

```bash
# Local/minikube
helm install acp ./helm \
  -f ./helm/values-local.yaml \
  --set azure.openai.endpoint="https://..." \
  --set azure.openai.apiKey="..." \
  --set agent.image.repository=myregistry/acp-agent \
  --set tokenServer.image.repository=myregistry/acp-token-server \
  --set frontend.image.repository=myregistry/acp-frontend

# Cloud (with ingress)
helm install acp ./helm \
  -f ./helm/values-cloud.yaml \
  --set azure.openai.endpoint="https://..." \
  --set azure.openai.apiKey="..." \
  --set frontend.ingress.host="acp.yourdomain.com" \
  --set agent.image.repository=myregistry/acp-agent \
  --set tokenServer.image.repository=myregistry/acp-token-server \
  --set frontend.image.repository=myregistry/acp-frontend
```

### Verify the Deployment

```bash
helm list
kubectl get pods
kubectl get svc
```

---

## 🏗 Architecture

```
┌──────────────┐     WebRTC     ┌────────────────────┐     Deepgram API      ┌──────────────┐
│   Frontend   │◄──────────────►│  LiveKit Server    │◄─────────────────────►│   Deepgram   │
│  (React/TS)  │                │   (Docker Local)   │  (api.au.deepgram.com)│  STT + TTS   │
│              │                │                    │  AWS Sydney           │  (Nova-3,    │
└──────────────┘                └────────┬───────────┘  ap-southeast-2       │  Aura-2)     │
                                         │                                   └──────────────┘
                                         │ Agent Dispatch (Redis)              Azure OpenAI
                                         │                                   ┌──────────────┐
                                 ┌───────▼────────┐                          │   Azure      │
                                 │  Voice Agent   │◄────────────────────────►│   OpenAI     │
                                 │   (Python)     │  Azure OpenAI API         │  (LLM)       │
                                 │ VAD→STT→LLM→TTS│  Australia East           │  gpt-4.1-mini│
                                 └────────────────┘                          └──────────────┘
```

### Components

| Component | Role | Technology |
|-----------|------|------------|
| **Frontend** | Web UI with microphone access | React + TypeScript + Vite |
| **LiveKit Server** | WebRTC media routing | Go (LiveKit) |
| **Redis** | Agent dispatch queue | Redis 7 |
| **Voice Agent** | AI pipeline: VAD → STT → LLM → TTS | Python (LiveKit Agents) |
| **Token Server** | Generates LiveKit access tokens | Python (aiohttp) |
| **Azure OpenAI** | LLM (conversation brain) | Cloud API (Australia East) |
| **Deepgram** | STT (Nova-3) + TTS (Aura-2) via Australian endpoint | Cloud API (AWS Sydney) |

### Data Flow (One Conversation Turn)

1. User speaks → browser mic → WebRTC audio → **LiveKit Server**
2. Agent receives audio → **Silero VAD** detects speech boundaries
3. Audio segments → **Deepgram STT** (Nova-3, via `api.au.deepgram.com`) → text transcript
4. Transcript → **Azure OpenAI LLM** (GPT-4.1-mini-aus, with ACP prompt) → response text
5. Response text → **Deepgram TTS** (Aura-2, via `api.au.deepgram.com`) → synthesised audio stream
6. Audio → LiveKit Server → WebRTC → user hears response

### Data Residency

- **LiveKit, Redis, Agent, Frontend**: Run on your local machine. No data leaves your computer.
- **Deepgram STT/TTS**: Voice data is sent to `api.au.deepgram.com` (AWS Sydney, ap-southeast-2). All audio stays in Australia. No data is stored — processed in real-time and discarded.
- **Azure OpenAI (LLM)**: When using **Australia East**, your text data is processed in Australian data centres in Sydney. No data is stored by Azure OpenAI — it is processed in real-time and discarded.

---

## ⚙️ Configuration Reference

### .env File

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_OPENAI_ENDPOINT` | ✅ | — | Your Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | ✅ | — | Your Azure OpenAI API key |
| `AZURE_OPENAI_API_VERSION` | ✅ | `2024-10-01-preview` | API version |
| `AZURE_OPENAI_LLM_DEPLOYMENT` | ✅ | `gpt-4.1-mini-aus` | LLM deployment name |
| `DEEPGRAM_API_KEY` | ✅ | — | Deepgram API key (for STT & TTS via Australian endpoint) |
| `LIVEKIT_API_KEY` | — | `devkey` | LiveKit API key (local default) |
| `LIVEKIT_API_SECRET` | — | `devsecret` | LiveKit API secret (local default) |

### Helm values.yaml

| Value | Default | Description |
|-------|---------|-------------|
| `azure.openai.endpoint` | `""` | Azure OpenAI endpoint (required) |
| `azure.openai.apiKey` | `""` | Azure OpenAI API key (required) |
| `azure.openai.apiVersion` | `2024-10-01-preview` | API version |
| `azure.openai.deployments.llm` | `gpt-4.1-mini-aus` | LLM deployment name |
| `deepgram.apiKey` | `""` | Deepgram API key (required for STT & TTS) |
| `livekit.apiKey` | `devkey` | LiveKit API key |
| `livekit.apiSecret` | `devsecret` | LiveKit API secret |
| `agent.replicas` | `1` | Number of agent replicas |
| `frontend.replicas` | `2` | Number of frontend replicas |
| `frontend.ingress.enabled` | `false` | Enable ingress for frontend |

---

## 🛠 Development Guide

### Running the Agent Locally (Without Docker)

```bash
cd agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start the agent (LiveKit must be running via docker compose)
python -m agent.main
```

### Running the Frontend Locally (Without Docker)

```bash
cd frontend
npm install
npm run dev
```

### Customising the Conversation Prompt

The AI's conversation style and topics are defined in **`agent/prompt.yaml`** — an easy-to-edit plain text file. You can change the tone, add or remove questions, or completely redesign the conversation flow.

**To customise:**
1. Open `agent/prompt.yaml` in any text editor
2. Edit the text under `prompt: |` — the vertical bar means everything indented below it is the prompt
3. Save the file
4. Rebuild the agent: `docker compose build agent && docker compose up -d agent`

**What you can change:**
- The AI's personality and tone
- The conversation phases and topics
- Specific questions asked
- Medical or ethical guidelines
- Language, cultural references, or terminology (e.g. Australian-specific healthcare terms)

**What is locked (do not modify):**
- The `TTS Output Rules` section is appended automatically by the code. These rules ensure the AI's responses sound natural when spoken by Azure OpenAI TTS. They cannot be edited through the YAML file.

**Prompt reloading:** The prompt is loaded once when the agent starts. After editing `prompt.yaml`, you must restart the agent (`docker compose restart agent`).

### Rebuilding After Changes

```bash
# Rebuild a specific service
docker compose build agent
docker compose up -d agent

# Or rebuild everything
docker compose build
docker compose up -d
```

---

## 🔍 Troubleshooting

### "Docker Engine is not running"
- Open **Docker Desktop** from your Start menu
- Wait for the green "Engine running" indicator
- Run the script again

### "Connection Error" in the browser
- Make sure all services are running: `docker compose ps`
- Check the agent logs: `docker compose logs agent`
- Verify your `.env` file has the correct Azure OpenAI credentials

### No audio / Can't hear the AI
- Check your browser's microphone permission (look for a mic icon in the address bar)
- Make sure your speakers are on and not muted
- Try using Chrome or Edge (some browsers handle WebRTC better)

### "Agent not registered" in logs
- Wait a few seconds — the agent connects to LiveKit on startup
- Check Redis is running: `docker compose logs redis`

### Need Help?
- Open an issue on the GitHub repository
- Include the output of: `docker compose logs --tail=50 agent`

---

## 📄 License

MIT

---

## 🙏 Acknowledgments

- [LiveKit](https://livekit.io) — Open-source WebRTC platform
- [Azure OpenAI](https://azure.microsoft.com/products/ai-services/openai-service) — LLM hosted in Australia East
- [Deepgram](https://deepgram.com) — STT and TTS via Australian endpoint (data stays in Sydney)
- [Advance Care Planning Australia](https://www.advancecareplanning.org.au) — National ACP advisory body
- Built as a reference architecture for the developer community

### Supporting Australian ACP

If you found this tool helpful, we encourage you to:
1. **Formalise your wishes** using your state or territory's official Advance Care Directive form
2. **Discuss your directive** with your GP, your substitute decision-maker, and your family
3. **Upload your directive** to [My Health Record](https://www.myhealthrecord.gov.au) so it's available to healthcare providers across Australia