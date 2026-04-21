#!/bin/bash
# Remote Deployment Script for zelkova
# USAGE: bash scripts/deploy-remote.sh
# Run this on the zelkova server after images are pushed to GHCR

set -e

echo "=============================================================="
echo "polypocket - Remote Deployment"
echo "=============================================================="
echo ""

# Configuration
REPO_DIR="${REPO_DIR:-.}"
REGISTRY="ghcr.io"
REPO_NAME="${REPO_NAME:-polypocket}"

echo "📋 Configuration:"
echo "  Repository: $REPO_NAME"
echo "  Registry: $REGISTRY"
echo "  Directory: $REPO_DIR"
echo ""

# 1. Navigate to repo
cd "$REPO_DIR" || exit 1

# 2. Pull latest code
echo "📥 Pulling latest code..."
git fetch origin
git pull origin master
echo "✓ Code updated"
echo ""

# 3. Load environment
echo "🔧 Loading environment..."
if [ -f .env ]; then
  echo "✓ .env file loaded"
else
  echo "⚠️  .env not found - using defaults"
fi
echo ""

# 4. Stop running services
echo "🛑 Stopping running services..."
docker compose down || true
echo "✓ Services stopped"
echo ""

# 5. Pull latest images from GHCR
echo "📦 Pulling latest images from GHCR..."
docker compose pull
echo "✓ Images pulled"
echo ""

# 6. Ensure volumes exist
echo "💾 Ensuring volumes exist..."
docker volume ls | grep polypocket_logs || docker volume create polypocket_logs
docker volume ls | grep polypocket_data || docker volume create polypocket_data
echo "✓ Volumes ready"
echo ""

# 7. Start services
echo "🚀 Starting services..."
docker compose up -d
echo "✓ Services started"
echo ""

# 8. Wait for services to be healthy
echo "⏳ Waiting for bot to be healthy..."
for i in {1..30}; do
  if docker compose ps bot | grep -q healthy || docker compose ps bot | grep -q running; then
    echo "  ✓ Bot is healthy"
    break
  fi
  sleep 2
done
echo ""

# 9. Verify deployment
echo "✅ Verifying deployment..."
echo ""
echo "Service Status:"
docker compose ps
echo ""

# 10. Show logs
echo "Recent logs:"
docker compose logs --tail=20 bot
echo ""

echo "=============================================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=============================================================="
echo ""
echo "Services running:"
echo "  Bot: polypocket"
echo ""
echo "View logs:"
echo "  docker compose logs -f bot"
echo ""
echo "Monitor performance:"
echo "  python report.py --days 7"
echo ""
