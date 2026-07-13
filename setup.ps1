<#
.SYNOPSIS
  ACP Setup Script - Auto-detect host IP for LiveKit
.DESCRIPTION
  Detects the host machine LAN IP and writes it to .env so that Docker
  Compose can pass it as --node-ip to the LiveKit server.
  Usage: .\setup.ps1
  Supports: Windows (PowerShell 5.1+)
#>

$ErrorActionPreference = "Stop"
$envPath = Join-Path $PSScriptRoot ".env"

Write-Host "Detecting host LAN IP..." -ForegroundColor Cyan

# Find the default route interface (Wi-Fi or Ethernet with DHCP)
$adapter = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.PrefixOrigin -eq 'Dhcp' } |
    Sort-Object InterfaceMetric |
    Select-Object -First 1

# Fallback: skip loopback, link-local, and well-known prefixes
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
    Write-Error "Could not detect host IP. Set HOST_IP manually in .env"
    exit 1
}

$HOST_IP = $adapter.IPAddress
Write-Host ("  Detected: " + $HOST_IP + " (on " + $adapter.InterfaceAlias + ")") -ForegroundColor Green

# Read or create .env
$content = @()
if (Test-Path $envPath) {
    $content = Get-Content $envPath
    $found = $false
    for ($i = 0; $i -lt $content.Count; $i++) {
        if ($content[$i] -match '^HOST_IP=') {
            $content[$i] = "HOST_IP=$HOST_IP"
            $found = $true
        }
    }
    if (-not $found) {
        $content += ""
        $content += ("# Auto-detected by setup.ps1 on " + (Get-Date -Format "yyyy-MM-dd"))
        $content += "HOST_IP=$HOST_IP"
    }
} else {
    $content += ""
    $content += ("# Auto-detected by setup.ps1 on " + (Get-Date -Format "yyyy-MM-dd"))
    $content += "HOST_IP=$HOST_IP"
}

$content | Set-Content -Path $envPath -Encoding UTF8
Write-Host ("Done. HOST_IP=" + $HOST_IP) -ForegroundColor Green