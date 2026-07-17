# 🚀 Deployment Guide

This document describes how to deploy the ACP Voice Assistant to production and local staging environments using Docker Compose or Kubernetes (with Helm).

## Option A: Local Deployment with Docker Compose

Docker Compose is the recommended way to run the entire stack for staging, testing, or offline clinician tablets.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- A filled out `.env` file in the root directory (see [Configuration Reference](configuration.md)).

### Start the Application
To build and start all 5 components in the background:
```bash
docker compose up -d
```
Docker Compose will download base images, build local containers for the `agent`, `token-server`, and `frontend`, and link them via an internal network.

### Checking Services Status
Verify that all containers are healthy:
```bash
docker compose ps
```
You should see:
* `redis`
* `livekit-server`
* `token-server`
* `agent`
* `frontend`

### Logging & Monitoring
To tail logs for all containers:
```bash
docker compose logs -f
```
To tail logs for a specific service:
```bash
docker compose logs -f agent
```

### Stop and Clean Up
To stop all running services:
```bash
docker compose down
```
To stop all services and **destroy all volumes** (clearing Redis databases and caching states):
```bash
docker compose down -v
```

---

## Option B: Kubernetes Deployment with Helm

For production environments requiring high availability, scalability, or deployment to cloud providers (AKS, EKS, GKE).

### Prerequisites
- A running Kubernetes cluster.
- [Helm 3](https://helm.sh/) installed locally.
- Access to a private or public Docker container registry (e.g., Azure Container Registry, Docker Hub).

### 1. Build and Push Container Images
First, build and tag the Docker images, then push them to your registry:
```bash
# Define your registry prefix
REGISTRY="myregistry.azurecr.io"

# Build local images
docker build -t $REGISTRY/acp-agent:latest ./agent
docker build -t $REGISTRY/acp-token-server:latest ./token-server
docker build -t $REGISTRY/acp-frontend:latest ./frontend

# Push images to the registry
docker push $REGISTRY/acp-agent:latest
docker push $REGISTRY/acp-token-server:latest
docker push $REGISTRY/acp-frontend:latest
```

### 2. Deploy Using Helm
Modify the values files inside the `helm/` directory or pass settings via `--set` arguments:

```bash
# Example deployment command specifying credentials and custom image repositories
helm install acp ./helm \
  -f ./helm/values-cloud.yaml \
  --set azure.openai.endpoint="https://your-endpoint.openai.azure.com" \
  --set azure.openai.apiKey="your-azure-key" \
  --set deepgram.apiKey="your-deepgram-key" \
  --set groq.apiKey="your-groq-key" \
  --set agent.image.repository=$REGISTRY/acp-agent \
  --set tokenServer.image.repository=$REGISTRY/acp-token-server \
  --set frontend.image.repository=$REGISTRY/acp-frontend \
  --set frontend.ingress.enabled=true \
  --set frontend.ingress.host="acp.yourdomain.com"
```

### 3. Verify the Deployment
Ensure all pods and services are running:
```bash
kubectl get pods -l app.kubernetes.io/instance=acp
kubectl get svc
kubectl get ingress
```
Once the Ingress controller provisions the external IP, navigate to your configured host domain (e.g., `https://acp.yourdomain.com`) to access the interface.
