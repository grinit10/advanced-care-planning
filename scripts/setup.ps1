# Advanced Care Planning — Local Setup Script
# Run this script to start everything: LiveKit, Redis, Agent, and Frontend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Advanced Care Planning — Voice AI" -ForegroundColor Cyan
Write-Host "  Local Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Docker
Write-Host "[1/4] Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "  ✅ Docker is installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker is not installed!" -ForegroundColor Red
    Write-Host "  Please download and install Docker Desktop from:" -ForegroundColor Red
    Write-Host "  https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
    Write-Host ""
    Write-Host "  After installing, open Docker Desktop and wait for it to say 'Engine running'."
    Write-Host "  Then run this script again."
    exit 1
}

# Check if Docker is running
try {
    $null = docker info 2>&1 | Out-Null
    Write-Host "  ✅ Docker Engine is running" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Docker Engine is not running." -ForegroundColor Yellow
    Write-Host "  Please open Docker Desktop and wait for 'Engine running'."
    exit 1
}

# Step 2: Check .env file
Write-Host "[2/4] Checking configuration..." -ForegroundColor Yellow
$envPath = Join-Path (Get-Location) ".env"
$envExamplePath = Join-Path (Get-Location) ".env.example"
if (-not (Test-Path $envPath)) {
    Write-Host "  ⚠️  .env file not found." -ForegroundColor Yellow
    if (Test-Path $envExamplePath) {
        Copy-Item $envExamplePath $envPath
        Write-Host "  ✅ Created .env from .env.example" -ForegroundColor Green
    } else {
        Write-Host "  ❌ .env.example not found either. Project may be incomplete." -ForegroundColor Red
        exit 1
    }
}

# Check if placeholder values remain in .env
$envContent = Get-Content $envPath -Raw
if ($envContent -match "your-api-key-here" -or $envContent -match "your-resource-name") {
    Write-Host "  ⚠️  Your .env file still has placeholder values!" -ForegroundColor Yellow
    Write-Host "  Opening .env for editing — replace the placeholders with your Azure OpenAI credentials." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Your Azure OpenAI endpoint looks like: https://YOUR-RESOURCE.openai.azure.com" -ForegroundColor Cyan
    Write-Host "  Your Azure OpenAI key looks like:      abc123def456..." -ForegroundColor Cyan
    Start-Process notepad.exe -ArgumentList $envPath
    Write-Host "  Press Enter AFTER you've saved the file to continue..." -ForegroundColor Yellow
    Read-Host
} else {
    Write-Host "  ✅ .env file looks configured" -ForegroundColor Green
}

# Step 3: Start Docker Compose
Write-Host "[3/4] Starting services with Docker Compose..." -ForegroundColor Yellow
Write-Host "  This will download images and start:"
Write-Host "  • Redis (message broker)"
Write-Host "  • LiveKit Server (WebRTC media)"
Write-Host "  • Voice Agent (AI processing)"
Write-Host "  • Token Server (authentication)"
Write-Host "  • Frontend (web interface)"
Write-Host ""

docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Failed to start services!" -ForegroundColor Red
    Write-Host "  Check the error above. Make sure Docker Desktop is running."
    exit 1
}

Write-Host "  ✅ Services started!" -ForegroundColor Green
Write-Host ""

# Step 4: Wait for services to be healthy
Write-Host "[4/5] Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$maxRetries = 12
$ready = $false
for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {}
    Write-Host "  ." -NoNewline
    Start-Sleep -Seconds 2
}

if ($ready) {
    Write-Host "  ✅ Frontend is ready!" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Frontend is taking longer than expected." -ForegroundColor Yellow
    Write-Host "  It may still be starting up. Check: docker compose logs frontend"
}

# Step 5: Open browser
Write-Host "[5/5] Opening the app..." -ForegroundColor Yellow
try {
    Start-Process "http://localhost:5173"
    Write-Host "  ✅ Browser opened!" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Could not open browser automatically." -ForegroundColor Yellow
    Write-Host "  Open http://localhost:5173 manually."
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All set! Here's what you can do:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  🌐 Open the app:     http://localhost:5173"
Write-Host ""
Write-Host "  📋 View agent logs:  docker compose logs -f agent"
Write-Host "  🛑 Stop everything:  docker compose down"
Write-Host "  ▶️  Restart later:   docker compose up -d"
Write-Host ""
Write-Host "  Need help? Check the README.md file."