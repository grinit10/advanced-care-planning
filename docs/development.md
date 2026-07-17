# 🛠 Development Guide

This guide details how to configure your local development environment to run, test, and customize the ACP Voice Assistant's UI and backend components separately.

## Prerequisites

Ensure you have the following installed on your host system:
- Python 3.12+ (or the `uv` tool for faster package management)
- Node.js 20+
- Git

---

## Rebuilding & Hot-Reloading Components Separately

Running UI and backend components separately allows you to benefit from hot-reloading (instant reload of code modifications) and enables easy debugging.

### Step 1: Run Backend Infrastructure
The Voice Agent and Token Server require local Redis and LiveKit servers to function. Run these in the background:
```bash
# Start infrastructure containers
docker compose up -d redis livekit-server
```

### Step 2: Run the Token Server (Local Python)
The React Frontend requests temporary credentials from the Token Server to join WebRTC rooms:
```bash
cd token-server
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```
*Note: The token server runs locally on port `8081`.*

### Step 3: Run the Voice Agent (Local Python)
Running the Voice Agent outside of Docker lets you inspect print logs, add debuggers, and modify LLM parameters instantly:
```bash
cd agent
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

# Start the agent in development/hot-reloads mode
python main.py dev
```
*Note: The agent worker will run and listen to LiveKit server dispatch events on port `8082`.*

### Step 4: Run the Frontend UI (Local Node.js)
Start the frontend development server to edit components with instant hot-reloading:
```bash
cd frontend
npm install

# Runs the web application on port 5173
npm run dev
```
Navigate to `http://localhost:5173` to test your changes.

---

## Customizing the Conversation Flow (`prompt.yaml`)

The AI's personality, tone, rules, and conversation phases are defined in a clean, human-readable YAML configuration file: **`agent/prompt.yaml`**.

### How to Edit:
1. Open `agent/prompt.yaml` in your favorite editor.
2. Edit the text under the `prompt: |` block.
3. Save the file.
4. Restart the agent:
   * **If running via Docker Compose:**
     ```bash
     docker compose restart agent
     ```
   * **If running locally without Docker:**
     Stop the script (`Ctrl+C`) and run `python main.py dev` again.

### What is Locked:
- The **`TTS Output Rules`** section is appended automatically at runtime by `prompt_loader.py`. These rules ensure that the AI formats text elements (like abbreviations, lists, or headers) to sound clean when read aloud by the Text-to-Speech system. Do not duplicate these rules in `prompt.yaml`.

---

## Running Linting and Formatting Checks

Before pushing code changes to GitHub, ensure all linters and formatting rules pass to keep the CI pipeline green.

```bash
cd agent

# Auto-format code formatting issues
uv run ruff format .

# Auto-fix linting and import ordering errors
uv run ruff check --fix .

# Verify type safety
uv run pyright .
```
