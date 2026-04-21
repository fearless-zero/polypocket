#!/bin/bash
# Auto-update script - pulls latest images and restarts containers
# Can be run manually or via cron: 0 */6 * * * /path/to/polypocket/scripts/auto-update.sh

set -e

cd "$(dirname "$0")/.."

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting auto-update..."

# Pull latest image
echo "Pulling latest image..."
docker pull ghcr.io/${GITHUB_REPOSITORY:-user/polypocket}:latest

# Restart services
echo "Restarting services..."
docker compose down
docker compose up -d

# Wait for services to be healthy
echo "Waiting for bot to be healthy..."
sleep 10

# Check health
if docker compose ps bot | grep -q running; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✓ Auto-update completed successfully"
    docker compose logs --tail=10 bot
    exit 0
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✗ Health check failed after update"
    docker compose logs --tail=50 bot
    exit 1
fi
