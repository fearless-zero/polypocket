# Deployment Guide

Complete guide for deploying polypocket to zelkova with CI/CD pipeline.

## Prerequisites

- GitHub repository with Actions enabled
- Docker and docker-compose on zelkova
- SSH access to zelkova
- GitHub Personal Access Token (for GHCR authentication)

## Architecture Overview

```
GitHub Actions (CI/CD)
  ↓
  1. Run tests (lint + pytest)
  2. Build Docker image
  3. Push to GHCR (GitHub Container Registry)
  ↓
zelkova (VPS)
  ↓
  1. Pull latest image from GHCR
  2. Restart containers
  3. Monitor health
```

## Step 1: Local Setup

### 1.1 Environment Configuration

Create a `.env` file (do NOT commit this):

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Polymarket CLOB API credentials
POLYMARKET_API_KEY=your_key_here
POLYMARKET_API_SECRET=your_secret_here
POLYMARKET_API_PASSPHRASE=your_passphrase_here

# Chainlink RPC (Polygon mainnet)
CHAINLINK_RPC=https://polygon-rpc.com
CHAINLINK_AGGREGATOR_ADDRESS=0xc907E116054Ad103354f2D350FD2514433D57F6f

# Trading parameters
BANKROLL=2000
PROFIT_TARGET=0.75
STOP_LOSS=0.35
ENTRY_WINDOW_MIN=60
ENTRY_WINDOW_MAX=180

# Signal thresholds
PRICE_DIVERGENCE_THRESHOLD=50
ORDER_BOOK_IMBALANCE_UP=1.8
ORDER_BOOK_IMBALANCE_DOWN=0.55
```

### 1.2 Test Locally

```bash
# Build and test locally
docker compose build
docker compose up -d

# Check logs
docker compose logs -f bot

# Stop
docker compose down
```

## Step 2: GitHub Setup

### 2.1 Repository Settings

Ensure your repository has GitHub Actions enabled:
- Go to `Settings` → `Actions` → `General`
- Set `Workflow permissions` to `Read and write permissions`

### 2.2 GitHub Secrets (Optional - for webhooks)

If you want automatic deployment via webhooks:

1. Go to `Settings` → `Secrets and variables` → `Actions`
2. Add these secrets/variables:

| Type | Name | Value | Purpose |
|------|------|-------|---------|
| Variable | `DEPLOYMENT_WEBHOOK_URL` | `https://zelkova.example.com/webhook` | Webhook endpoint (optional) |
| Secret | `DEPLOYMENT_WEBHOOK_TOKEN` | `your-secure-token` | Webhook auth (optional) |

## Step 3: zelkova Setup

### 3.1 Install Docker & Docker Compose

On zelkova:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### 3.2 Clone Repository

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/polypocket.git
cd polypocket
```

### 3.3 Configure Environment

```bash
# Copy and edit .env
cp .env.example .env
nano .env  # Fill in your API keys
```

### 3.4 Authenticate with GHCR

Create a GitHub Personal Access Token (PAT):
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `read:packages` scope
3. Copy the token

On zelkova:

```bash
# Login to GHCR
echo "YOUR_GITHUB_PAT" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Set GITHUB_REPOSITORY environment variable
export GITHUB_REPOSITORY="YOUR_USERNAME/polypocket"
echo "export GITHUB_REPOSITORY='YOUR_USERNAME/polypocket'" >> ~/.bashrc
```

## Step 4: First Deployment

### 4.1 Push to GitHub (triggers CI/CD)

On your local machine:

```bash
# Stage all changes
git add .

# Commit
git commit -m "feat: add Docker and CI/CD pipeline"

# Push to master (triggers GitHub Actions)
git push origin master
```

This triggers the CI/CD pipeline:
1. ✅ Lint with ruff
2. ✅ Run tests
3. 📦 Build Docker image
4. 🚀 Push to GHCR

### 4.2 Deploy on zelkova

Once GitHub Actions completes successfully:

```bash
# SSH to zelkova
ssh zelkova

# Navigate to repo
cd ~/polypocket

# Run deployment script
bash scripts/deploy-remote.sh
```

The script will:
- Pull latest code
- Pull latest Docker image from GHCR
- Stop old containers
- Start new containers
- Verify health

## Step 5: Verify Deployment

### 5.1 Check Service Status

```bash
# View running containers
docker compose ps

# Expected output:
# NAME              STATUS              PORTS
# polypocket        Up (healthy)
```

### 5.2 Monitor Logs

```bash
# Follow live logs
docker compose logs -f bot

# View last 50 lines
docker compose logs --tail=50 bot
```

### 5.3 Check Trading Activity

```bash
# Generate performance report (after some trades)
python report.py --days 7

# Analyze order book patterns
python analyze_orderbook.py --windows 1000
```

## Step 6: Automatic Updates (Optional)

### 6.1 Setup Cron Job

On zelkova, schedule automatic updates every 6 hours:

```bash
# Edit crontab
crontab -e

# Add this line:
0 */6 * * * cd ~/polypocket && bash scripts/auto-update.sh >> ~/polypocket/logs/auto-update.log 2>&1
```

This will:
- Pull latest image from GHCR every 6 hours
- Restart containers
- Log results to `logs/auto-update.log`

### 6.2 Setup Webhook (Advanced)

For instant deployment after GitHub pushes, set up a webhook listener on zelkova.

Example using a simple webhook service:

```bash
# Install webhook tool
sudo apt install webhook -y

# Create webhook config
cat > ~/webhook.json <<EOF
[
  {
    "id": "polypocket-deploy",
    "execute-command": "/home/YOUR_USER/polypocket/scripts/deploy-remote.sh",
    "command-working-directory": "/home/YOUR_USER/polypocket",
    "response-message": "Deploying polypocket...",
    "trigger-rule": {
      "match": {
        "type": "value",
        "value": "YOUR_WEBHOOK_SECRET",
        "parameter": {
          "source": "payload",
          "name": "token"
        }
      }
    }
  }
]
EOF

# Run webhook service
webhook -hooks ~/webhook.json -verbose -port 9000
```

Then configure GitHub to send webhooks to `http://zelkova.example.com:9000/hooks/polypocket-deploy`.

## Maintenance

### View Logs

```bash
# Live logs
docker compose logs -f bot

# Last 100 lines
docker compose logs --tail=100 bot

# Logs with timestamps
docker compose logs -f --timestamps bot
```

### Restart Services

```bash
# Restart bot
docker compose restart bot

# Full restart (pull latest image)
bash scripts/auto-update.sh
```

### Update Configuration

```bash
# Edit .env
nano .env

# Restart to apply changes
docker compose restart bot
```

### Backup Data

```bash
# Backup logs and data
tar -czf polypocket-backup-$(date +%Y%m%d).tar.gz logs/ data/

# Backup to remote storage
scp polypocket-backup-*.tar.gz backup-server:/backups/
```

### Troubleshooting

#### Container won't start

```bash
# Check logs
docker compose logs bot

# Rebuild image
docker compose build --no-cache bot
docker compose up -d
```

#### GHCR authentication failed

```bash
# Re-authenticate
echo "YOUR_GITHUB_PAT" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Pull manually
docker pull ghcr.io/YOUR_USERNAME/polypocket:latest
```

#### Out of disk space

```bash
# Clean up old images
docker system prune -a

# Remove old logs
find logs/ -type f -mtime +30 -delete
```

## Monitoring

### Resource Usage

```bash
# Container stats
docker stats polypocket

# Disk usage
docker system df
```

### Performance Metrics

```bash
# Generate report
python report.py --days 30

# Check win rate
grep "PROFIT\|LOSS" logs/*.log | wc -l
```

## Files Reference

- `.github/workflows/ci.yml` - CI/CD pipeline
- `docker-compose.yml` - Docker services configuration
- `Dockerfile` - Container image definition
- `.dockerignore` - Files excluded from Docker build
- `scripts/deploy-remote.sh` - Deployment script for zelkova
- `scripts/auto-update.sh` - Automatic update script
- `DEPLOYMENT.md` - This guide

## Security Notes

- **Never commit `.env`** - Contains API keys
- **Use strong passwords** - For database and API keys
- **Keep PAT secure** - GitHub Personal Access Token has read access to packages
- **Regular updates** - Keep Docker and dependencies up to date
- **Monitor logs** - Watch for unusual activity

## Next Steps

After successful deployment:

1. Monitor first few trades to verify strategy is working
2. Adjust parameters in `.env` based on performance
3. Set up automated backups
4. Configure alerts (email/Slack) for trade notifications
5. Review logs daily for the first week

---

**Questions?** Check the main README.md or open an issue on GitHub.
