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

# Step 2: Check .env file and detect IP/Ports
Write-Host "[2/5] Checking configuration and network ports..." -ForegroundColor Yellow
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

# 2a. Detect Host LAN IP
Write-Host "  🔍 Detecting host LAN IP..." -ForegroundColor Yellow
$adapter = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.PrefixOrigin -eq 'Dhcp' } |
    Sort-Object InterfaceMetric |
    Select-Object -First 1

if (-not $adapter) {
    $adapter = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.InterfaceAlias -notlike '*Loopback*' -and
                       $_.PrefixOrigin -ne 'WellKnown' -and
                       $_.IPAddress -notlike '169.254.*' -and
                       $_.IPAddress -notlike '127.*' } |
        Sort-Object InterfaceMetric |
        Select-Object -First 1
}

if (-not $adapter) {
    Write-Host "  ⚠️  Could not detect host IP automatically. Set HOST_IP manually in .env" -ForegroundColor Yellow
    $HOST_IP = ""
} else {
    $HOST_IP = $adapter.IPAddress
    Write-Host "  ✅ Detected host IP: $HOST_IP (on $($adapter.InterfaceAlias))" -ForegroundColor Green
}

# 2b. Check Port Availability for Frontend
Write-Host "  🔍 Checking port availability for frontend..." -ForegroundColor Yellow
$FRONTEND_PORT = 5173
while ($true) {
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $FRONTEND_PORT)
        $listener.Start()
        $listener.Stop()
        break
    } catch {
        Write-Host "  ⚠️  Port $FRONTEND_PORT is already in use. Trying next port..." -ForegroundColor Yellow
        $FRONTEND_PORT++
    }
}
Write-Host "  ✅ Selected port: $FRONTEND_PORT" -ForegroundColor Green

# 2c. Write/Update .env
$content = Get-Content $envPath
$updatedHostIp = $false
$updatedPort = $false

for ($i = 0; $i -lt $content.Count; $i++) {
    if ($content[$i] -match '^HOST_IP=') {
        if ($HOST_IP) {
            $content[$i] = "HOST_IP=$HOST_IP"
        }
        $updatedHostIp = $true
    }
    if ($content[$i] -match '^FRONTEND_PORT=') {
        $content[$i] = "FRONTEND_PORT=$FRONTEND_PORT"
        $updatedPort = $true
    }
}

$newContent = @()
foreach ($line in $content) {
    $newContent += $line
}

if (-not $updatedHostIp -and $HOST_IP) {
    $newContent += "HOST_IP=$HOST_IP"
}
if (-not $updatedPort) {
    $newContent += "FRONTEND_PORT=$FRONTEND_PORT"
}

$newContent | Set-Content -Path $envPath -Encoding UTF8

# Check if placeholder values remain in .env
$envContent = Get-Content $envPath -Raw
if ($envContent -match "your-api-key-here" -or $envContent -match "your-resource-name") {
    Write-Host "  ⚠️  Your .env file still has placeholder values!" -ForegroundColor Yellow
    Write-Host "  Opening .env for editing — replace the placeholders with your credentials." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Your Azure OpenAI endpoint looks like: https://YOUR-RESOURCE.openai.azure.com" -ForegroundColor Cyan
    Write-Host "  Your Azure OpenAI key looks like:      abc123def456..." -ForegroundColor Cyan
    Start-Process notepad.exe -ArgumentList $envPath
    Write-Host "  Press Enter AFTER you've saved the file to continue..." -ForegroundColor Yellow
    Read-Host
} else {
    Write-Host "  ✅ .env file configured" -ForegroundColor Green
}

# Step 3: Start Docker Compose
Write-Host "[3/5] Starting services with Docker Compose..." -ForegroundColor Yellow
Write-Host "  This will download images and start:"
Write-Host "  • Redis (message broker)"
Write-Host "  • LiveKit Server (WebRTC media)"
Write-Host "  • Voice Agent (AI processing)"
Write-Host "  • Token Server (authentication)"
Write-Host "  • Frontend (web interface on port $FRONTEND_PORT)"
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
        $response = Invoke-WebRequest -Uri "http://localhost:$FRONTEND_PORT" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
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
    Start-Process "http://localhost:$FRONTEND_PORT"
    Write-Host "  ✅ Browser opened!" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Could not open browser automatically." -ForegroundColor Yellow
    Write-Host "  Open http://localhost:$FRONTEND_PORT manually."
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All set! Here's what you can do:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  🌐 Open the app:     http://localhost:$FRONTEND_PORT"
Write-Host ""
Write-Host "  📋 View agent logs:  docker compose logs -f agent"
Write-Host "  🛑 Stop everything:  docker compose down"
Write-Host "  ▶️  Restart later:   docker compose up -d"
Write-Host ""
Write-Host "  Need help? Check the README.md file."