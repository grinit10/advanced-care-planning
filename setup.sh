#!/bin/bash
# =============================================================================
# ACP Setup Script — Auto-detect host IP for LiveKit
# =============================================================================
# Detects the host machine's LAN IP and writes it to .env so that Docker
# Compose can pass it as --node-ip to the LiveKit server.
#
# Usage:
#   ./setup.sh
#   docker compose up -d
#
# Supported: Linux, macOS
# Windows users: run setup.ps1 instead
# =============================================================================

set -euo pipefail

detect_ip() {
  # Linux: IP on the default route
  if command -v ip &>/dev/null; then
    local ip
    ip=$(ip -4 route get 1 2>/dev/null | awk '{print $NF; exit}')
    if [ -n "$ip" ] && [ "$ip" != "0.0.0.0" ]; then
      echo "$ip"
      return 0
    fi
  fi

  # macOS: use route + ifconfig
  if command -v route &>/dev/null && command -v ifconfig &>/dev/null; then
    local iface ip
    iface=$(route -n get default 2>/dev/null | awk '/interface:/ {print $2}')
    if [ -n "$iface" ]; then
      ip=$(ifconfig "$iface" 2>/dev/null | awk '/inet /{print $2; exit}')
      if [ -n "$ip" ]; then
        echo "$ip"
        return 0
      fi
    fi
  fi

  # Fallback: hostname -I
  if command -v hostname &>/dev/null; then
    local ip
    ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    if [ -n "$ip" ] && [ "$ip" != "127.0.0.1" ]; then
      echo "$ip"
      return 0
    fi
  fi

  return 1
}

# --- Main ---

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

echo "🔍 Detecting host LAN IP..."

HOST_IP=$(detect_ip) || {
  echo "❌ Could not detect host IP automatically."
  echo ""
  echo "  Set HOST_IP manually in $ENV_FILE:"
  echo "    HOST_IP=192.168.1.42"
  echo ""
  echo "  Find your IP with: ip addr | grep 'inet ' (Linux)"
  echo "  or: ifconfig (macOS)"
  exit 1
}

echo "  → Detected: $HOST_IP"

# Write to .env (create or update)
if [ -f "$ENV_FILE" ] && grep -q "^HOST_IP=" "$ENV_FILE" 2>/dev/null; then
  # Update existing HOST_IP line
  sed -i.bak "s/^HOST_IP=.*$/HOST_IP=$HOST_IP/" "$ENV_FILE"
  rm -f "$ENV_FILE.bak"
  echo "  → Updated HOST_IP in existing .env"
elif [ -f "$ENV_FILE" ]; then
  # Append to existing .env
  echo "" >> "$ENV_FILE"
  echo "# Auto-detected by setup.sh on $(date)" >> "$ENV_FILE"
  echo "HOST_IP=$HOST_IP" >> "$ENV_FILE"
  echo "  → Appended HOST_IP to .env"
else
  # Create new .env from example
  if [ -f "$SCRIPT_DIR/.env.example" ]; then
    cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
    # Remove any existing HOST_IP line from example
    sed -i.bak '/^HOST_IP=/d' "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
  fi
  echo "" >> "$ENV_FILE"
  echo "# Auto-detected by setup.sh on $(date)" >> "$ENV_FILE"
  echo "HOST_IP=$HOST_IP" >> "$ENV_FILE"
  echo "  → Created .env with HOST_IP"
fi

echo ""
echo "✅ Setup complete. Start the app with:"
echo "   docker compose up -d"