# Week 10 Webhook Sync - Quick Start Guide

## Prerequisites

- Python 3.14+
- Redis server
- Zoho CRM access
- Cognee instance

## 1. Installation

```bash
# Install dependencies (already in pyproject.toml)
poetry install

# Or with pip
pip install -r requirements.txt
```

## 2. Configuration

```bash
# Generate webhook secret
python -c "import secrets; print(f'WEBHOOK_SECRET={secrets.token_hex(32)}')"

# Add to .env
echo "WEBHOOK_SECRET=<generated-secret>" >> .env
echo "WEBHOOK_BASE_URL=https://your-domain.com" >> .env
echo "REDIS_HOST=localhost" >> .env
echo "REDIS_PORT=6379" >> .env
```

## 3. Start Services

```bash
# Terminal 1: Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 2: Start FastAPI
uvicorn src.main:app --reload --port 8000

# Terminal 3: Start webhook processor
python -m src.sync.processor
```

## 4. Test Webhook

```bash
# Health check
curl http://localhost:8000/webhooks/health

# Send test webhook
python << 'PYEOF'
import requests
import json
import hmac
import hashlib
import os

payload = {
    "operation": "create",
    "module": "Accounts",
    "data": [{"id": "test_123", "Account_Name": "Test Corp"}]
}

payload_str = json.dumps(payload)
secret = os.getenv("WEBHOOK_SECRET")
signature = hmac.new(secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()

response = requests.post(
    "http://localhost:8000/webhooks/zoho",
    data=payload_str,
    headers={
        "X-Zoho-Signature": signature,
        "X-Zoho-Event-Id": "test_event_1",
        "Content-Type": "application/json"
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
PYEOF
```

## 5. Monitor

```bash
# View metrics
curl http://localhost:8000/webhooks/metrics

# Check Redis queue
redis-cli LLEN webhook:queue
```

## Next Steps

- Register webhooks with Zoho CRM
- Configure production environment
- Set up monitoring dashboards
- Review full documentation in `week10_webhook_sync_implementation.md`
