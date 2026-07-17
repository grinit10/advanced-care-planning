# ⚙️ Configuration Reference

This document provides a comprehensive reference of all environment variables and configuration parameters used by the ACP Voice Assistant.

## Environment Variables (`.env`)

You must configure a `.env` file in the root of the project to supply required third-party API keys and customize deployment properties.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_OPENAI_ENDPOINT` | ✅ | — | The endpoint URL of your Azure OpenAI resource (e.g. `https://acp-openai.openai.azure.com`). |
| `AZURE_OPENAI_API_KEY` | ✅ | — | The primary or secondary API access key for Azure OpenAI. |
| `AZURE_OPENAI_API_VERSION` | ✅ | `2024-10-01-preview` | The API version used when calling Azure OpenAI. |
| `AZURE_OPENAI_LLM_DEPLOYMENT` | ✅ | `gpt-4.1-mini-aus` | The name of your GPT-4o-mini (or similar) deployment for background extraction and summary generation. |
| `GROQ_API_KEY` | ✅ | — | The API key for your Groq Console account. |
| `GROQ_VOICE_MODEL` | — | `llama-3.1-8b-instant` | The model used for low-latency chat interactions. |
| `DEEPGRAM_API_KEY` | ✅ | — | Your Deepgram API key used for STT and TTS services. |
| `LIVEKIT_API_KEY` | — | `devkey` | The API key used to secure LiveKit communication. |
| `LIVEKIT_API_SECRET` | — | `devsecret` | The API secret corresponding to `LIVEKIT_API_KEY`. |
| `ACS_CONNECTION_STRING` | — | — | *Optional.* Connection string for Azure Communication Services Email (for sending generated plans). |
| `ACS_SENDER_DOMAIN` | — | — | *Optional.* Verified sender domain under your Azure Communication Services resource (e.g., `DoNotReply@yourdomain.azurecomm.net`). |

---

## Helm Chart Configuration (`values.yaml`)

When deploying to Kubernetes, the Helm chart located in `helm/` exposes the following configuration settings:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `azure.openai.endpoint` | `""` | Azure OpenAI endpoint URL. |
| `azure.openai.apiKey` | `""` | Azure OpenAI API access key. |
| `azure.openai.apiVersion` | `2024-10-01-preview` | Azure OpenAI API version. |
| `azure.openai.deployments.llm` | `gpt-4.1-mini-aus` | The model deployment name to use. |
| `deepgram.apiKey` | `""` | Deepgram API access key. |
| `groq.apiKey` | `""` | Groq Cloud API access key. |
| `livekit.apiKey` | `devkey` | Secure token server API key. |
| `livekit.apiSecret` | `devsecret` | Secure token server API secret. |
| `agent.image.repository` | `acp-agent` | Docker image repository for the Voice Agent. |
| `agent.image.tag` | `latest` | Tag for the Voice Agent Docker image. |
| `agent.replicas` | `1` | Number of running agent worker pods. |
| `frontend.image.repository` | `acp-frontend` | Docker image repository for the React UI. |
| `frontend.image.tag` | `latest` | Tag for the Frontend Docker image. |
| `frontend.replicas` | `2` | Number of running web UI server pods. |
| `frontend.ingress.enabled` | `false` | Enable Kubernetes Ingress to expose the UI to the internet. |
| `frontend.ingress.host` | `acp.local` | The target hostname for Ingress routing. |
