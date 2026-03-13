#!/bin/bash
# Auto-restart Cloudflare tunnel for backend
# Usage: bash scripts/tunnel.sh
# Keeps tunnel alive - restarts if it dies

while true; do
  echo "[$(date)] Starting Cloudflare tunnel..."
  cloudflared tunnel --url http://localhost:8000 2>&1 | tee /tmp/tunnel.log
  echo "[$(date)] Tunnel died. Restarting in 5s..."
  sleep 5
done
