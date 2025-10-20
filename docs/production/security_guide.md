# Security Operations Guide

## Overview

This guide covers security operations, best practices, and incident response procedures for the Sergas Super Account Manager production system.

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Access Control](#access-control)
3. [Secrets Management](#secrets-management)
4. [Data Protection](#data-protection)
5. [Security Monitoring](#security-monitoring)
6. [Incident Response](#incident-response)
7. [Compliance](#compliance)
8. [Security Checklist](#security-checklist)

---

## Security Architecture

### Defense in Depth

```
┌──────────────────────────────────────────────────────────────┐
│ Layer 1: Perimeter Security                                  │
│  • Firewall (ports 80/443 only)                             │
│  • DDoS protection (Cloudflare/AWS Shield)                  │
│  • Geographic restrictions                                   │
│  • IP allowlisting (admin access)                           │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│ Layer 2: Transport Security                                  │
│  • TLS 1.3 only                                             │
│  • Certificate pinning                                       │
│  • Perfect forward secrecy                                   │
│  • HSTS headers                                             │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│ Layer 3: Application Security                                │
│  • OAuth 2.0 authentication                                  │
│  • JWT token validation                                      │
│  • Rate limiting (60 req/min)                               │
│  • Input validation                                          │
│  • CORS policies                                            │
│  • Security headers (CSP, X-Frame-Options)                  │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│ Layer 4: Business Logic Security                             │
│  • Approval gates for CRM writes                            │
│  • PII detection and masking                                │
│  • Compliance validation                                     │
│  • Read-only agent tools                                    │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│ Layer 5: Data Security                                       │
│  • Encryption at rest (AES-256-GCM)                         │
│  • Column-level encryption (PII)                            │
│  • Database access controls                                  │
│  • Audit logging (immutable)                                │
│  • Backup encryption                                         │
└──────────────────────────────────────────────────────────────┘
```

---

## Access Control

### Role-Based Access Control (RBAC)

#### Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **Admin** | System administrators | All permissions |
| **Account Executive** | Account managers | Read accounts, approve recommendations |
| **Manager** | Team managers | Read all accounts, bulk operations |
| **Viewer** | Read-only access | View accounts and recommendations |
| **API User** | Programmatic access | API access with limited permissions |

#### Permission Model

```python
# src/security/permissions.py

class Permission:
    # Account permissions
    ACCOUNT_READ = "account:read"
    ACCOUNT_LIST = "account:list"
    ACCOUNT_ANALYZE = "account:analyze"
    ACCOUNT_UPDATE = "account:update"

    # Recommendation permissions
    RECOMMENDATION_READ = "recommendation:read"
    RECOMMENDATION_APPROVE = "recommendation:approve"
    RECOMMENDATION_REJECT = "recommendation:reject"

    # Agent permissions
    AGENT_EXECUTE = "agent:execute"
    AGENT_VIEW_LOGS = "agent:view_logs"

    # Admin permissions
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    SYSTEM_CONFIGURE = "system:configure"

ROLE_PERMISSIONS = {
    "admin": [
        Permission.ACCOUNT_READ,
        Permission.ACCOUNT_LIST,
        Permission.ACCOUNT_ANALYZE,
        Permission.ACCOUNT_UPDATE,
        Permission.RECOMMENDATION_READ,
        Permission.RECOMMENDATION_APPROVE,
        Permission.RECOMMENDATION_REJECT,
        Permission.AGENT_EXECUTE,
        Permission.AGENT_VIEW_LOGS,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.SYSTEM_CONFIGURE,
    ],
    "account_executive": [
        Permission.ACCOUNT_READ,
        Permission.ACCOUNT_ANALYZE,
        Permission.RECOMMENDATION_READ,
        Permission.RECOMMENDATION_APPROVE,
        Permission.RECOMMENDATION_REJECT,
    ],
    "manager": [
        Permission.ACCOUNT_READ,
        Permission.ACCOUNT_LIST,
        Permission.ACCOUNT_ANALYZE,
        Permission.RECOMMENDATION_READ,
        Permission.AGENT_VIEW_LOGS,
    ],
    "viewer": [
        Permission.ACCOUNT_READ,
        Permission.RECOMMENDATION_READ,
    ],
}
```

### Authentication

#### OAuth 2.0 Flow

1. **Client requests authorization**
   ```http
   GET /oauth/authorize
     ?client_id=CLIENT_ID
     &response_type=code
     &redirect_uri=REDIRECT_URI
     &scope=account:read+recommendation:approve
   ```

2. **User authenticates and grants permission**

3. **Authorization code returned**
   ```http
   HTTP/1.1 302 Found
   Location: REDIRECT_URI?code=AUTH_CODE
   ```

4. **Client exchanges code for token**
   ```http
   POST /oauth/token
   Content-Type: application/x-www-form-urlencoded

   grant_type=authorization_code
   &code=AUTH_CODE
   &client_id=CLIENT_ID
   &client_secret=CLIENT_SECRET
   &redirect_uri=REDIRECT_URI
   ```

5. **Access token issued**
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIs...",
     "token_type": "Bearer",
     "expires_in": 3600,
     "refresh_token": "refresh_token_here",
     "scope": "account:read recommendation:approve"
   }
   ```

#### JWT Token Structure

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "USR-456",
    "email": "user@example.com",
    "role": "account_executive",
    "permissions": ["account:read", "recommendation:approve"],
    "iat": 1697720400,
    "exp": 1697724000
  },
  "signature": "..."
}
```

#### Token Validation

```python
# src/security/auth.py
from jose import jwt, JWTError
from datetime import datetime

async def validate_token(token: str) -> dict:
    """Validate JWT token and return claims."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Check expiration
        if datetime.fromtimestamp(payload['exp']) < datetime.now():
            raise HTTPException(status_code=401, detail="Token expired")

        # Check required claims
        required = ['sub', 'email', 'role', 'permissions']
        if not all(claim in payload for claim in required):
            raise HTTPException(status_code=401, detail="Invalid token")

        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### API Key Authentication

For programmatic access:

```python
# Generate API key
import secrets

api_key = f"sk_{secrets.token_urlsafe(32)}"
# Store hash in database
api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

# Validate API key
@app.middleware("http")
async def api_key_auth(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        api_key = request.headers.get("X-API-Key")
        if not api_key or not validate_api_key(api_key):
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API key"}
            )
    return await call_next(request)
```

---

## Secrets Management

### AWS Secrets Manager Integration

#### Store Secrets

```bash
# Create secret
aws secretsmanager create-secret \
  --name sergas/production/app-secrets \
  --description "Sergas production application secrets" \
  --secret-string '{
    "database_password": "strong_password_here",
    "redis_password": "redis_password_here",
    "secret_key": "jwt_secret_key_here",
    "webhook_secret": "webhook_signing_secret"
  }'

# Create Zoho credentials secret
aws secretsmanager create-secret \
  --name sergas/production/zoho-credentials \
  --secret-string '{
    "client_id": "zoho_client_id",
    "client_secret": "zoho_client_secret",
    "refresh_token": "zoho_refresh_token"
  }'

# Create Anthropic API key secret
aws secretsmanager create-secret \
  --name sergas/production/anthropic-key \
  --secret-string '{
    "api_key": "anthropic_api_key_here"
  }'
```

#### Retrieve Secrets

```python
# src/security/secrets.py
import boto3
import json
from functools import lru_cache

class SecretsManager:
    def __init__(self):
        self.client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)
        self._cache = {}

    @lru_cache(maxsize=10)
    def get_secret(self, secret_name: str) -> dict:
        """Retrieve and cache secret from AWS Secrets Manager."""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise

    def get_database_credentials(self) -> dict:
        """Get database credentials."""
        return self.get_secret(f"sergas/{settings.ENV}/app-secrets")

    def get_zoho_credentials(self) -> dict:
        """Get Zoho CRM credentials."""
        return self.get_secret(f"sergas/{settings.ENV}/zoho-credentials")

    def get_anthropic_key(self) -> str:
        """Get Anthropic API key."""
        secret = self.get_secret(f"sergas/{settings.ENV}/anthropic-key")
        return secret['api_key']

# Usage
secrets = SecretsManager()
db_creds = secrets.get_database_credentials()
DATABASE_PASSWORD = db_creds['database_password']
```

#### Secret Rotation

```python
# scripts/rotate_secrets.py
import boto3
import secrets as py_secrets

def rotate_jwt_secret():
    """Rotate JWT signing secret."""
    client = boto3.client('secretsmanager')

    # Generate new secret
    new_secret = py_secrets.token_urlsafe(32)

    # Update in Secrets Manager
    client.update_secret(
        SecretId='sergas/production/app-secrets',
        SecretString=json.dumps({
            'secret_key': new_secret,
            # ... other secrets
        })
    )

    # Trigger application restart to pick up new secret
    # kubectl rollout restart deployment sergas-app

# Run monthly
# 0 2 1 * * python scripts/rotate_secrets.py
```

---

## Data Protection

### Encryption at Rest

#### Database Encryption

```sql
-- Enable PostgreSQL encryption
ALTER DATABASE sergas_prod SET default_table_access_method = 'pgcrypto';

-- Encrypt sensitive columns
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create encrypted column
ALTER TABLE accounts ADD COLUMN email_encrypted bytea;

-- Encrypt data
UPDATE accounts SET email_encrypted = pgp_sym_encrypt(
    email,
    current_setting('app.encryption_key')
);

-- Decrypt data
SELECT pgp_sym_decrypt(email_encrypted, current_setting('app.encryption_key'))
FROM accounts;
```

#### Application-Level Encryption

```python
# src/security/encryption.py
from cryptography.fernet import Fernet
import base64

class DataEncryption:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)

    def encrypt(self, data: str) -> str:
        """Encrypt data."""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data."""
        decoded = base64.b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(decoded)
        return decrypted.decode()

# Usage
encryption = DataEncryption(settings.ENCRYPTION_KEY)

# Encrypt PII before storing
encrypted_email = encryption.encrypt(user.email)

# Decrypt when needed
decrypted_email = encryption.decrypt(encrypted_email)
```

### PII Detection and Masking

```python
# src/security/pii.py
import re

class PIIDetector:
    """Detect and mask personally identifiable information."""

    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERN = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    SSN_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b'
    CREDIT_CARD_PATTERN = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'

    @staticmethod
    def mask_email(text: str) -> str:
        """Mask email addresses."""
        return re.sub(
            PIIDetector.EMAIL_PATTERN,
            lambda m: f"{m.group(0)[0]}***@{m.group(0).split('@')[1]}",
            text
        )

    @staticmethod
    def mask_phone(text: str) -> str:
        """Mask phone numbers."""
        return re.sub(PIIDetector.PHONE_PATTERN, "***-***-****", text)

    @staticmethod
    def detect_pii(text: str) -> list:
        """Detect all PII in text."""
        findings = []

        if re.search(PIIDetector.EMAIL_PATTERN, text):
            findings.append({"type": "email", "severity": "high"})

        if re.search(PIIDetector.PHONE_PATTERN, text):
            findings.append({"type": "phone", "severity": "medium"})

        if re.search(PIIDetector.SSN_PATTERN, text):
            findings.append({"type": "ssn", "severity": "critical"})

        if re.search(PIIDetector.CREDIT_CARD_PATTERN, text):
            findings.append({"type": "credit_card", "severity": "critical"})

        return findings

    @staticmethod
    def sanitize(text: str) -> str:
        """Remove all PII from text."""
        text = PIIDetector.mask_email(text)
        text = PIIDetector.mask_phone(text)
        text = re.sub(PIIDetector.SSN_PATTERN, "***-**-****", text)
        text = re.sub(PIIDetector.CREDIT_CARD_PATTERN, "****-****-****-****", text)
        return text

# Usage in logging
logger.info(
    "account_data_retrieved",
    account_id="ACC-123",
    data=PIIDetector.sanitize(account_data)
)
```

### Audit Logging

```python
# src/security/audit.py
from datetime import datetime
import hashlib

class AuditLogger:
    """Immutable audit logging."""

    @staticmethod
    async def log_action(
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict,
        ip_address: str
    ):
        """Log security-relevant action."""

        # Create audit entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "ip_address": ip_address,
        }

        # Calculate hash for tamper detection
        entry_hash = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest()

        entry["hash"] = entry_hash

        # Store in database (append-only table)
        await db.audit_logs.insert(entry)

        # Also send to external log storage (S3, etc.)
        await send_to_external_storage(entry)

# Usage
await AuditLogger.log_action(
    user_id=current_user.id,
    action="recommendation.approved",
    resource_type="recommendation",
    resource_id=recommendation.id,
    details={
        "account_id": recommendation.account_id,
        "type": recommendation.type,
        "modifications": modifications
    },
    ip_address=request.client.host
)
```

---

## Security Monitoring

### Security Events to Monitor

```python
# src/security/monitoring.py

# Track authentication failures
auth_failures_total = Counter(
    'sergas_auth_failures_total',
    'Total authentication failures',
    ['reason', 'ip_address']
)

# Track authorization denials
authz_denials_total = Counter(
    'sergas_authz_denials_total',
    'Total authorization denials',
    ['user_id', 'resource', 'action']
)

# Track PII access
pii_access_total = Counter(
    'sergas_pii_access_total',
    'Total PII access events',
    ['user_id', 'resource_type']
)

# Track suspicious activity
suspicious_activity = Counter(
    'sergas_suspicious_activity_total',
    'Suspicious activity detected',
    ['type', 'severity']
)
```

### Security Alerts

```yaml
# /etc/prometheus/security-alerts.yml
groups:
  - name: security_alerts
    interval: 30s
    rules:
      # Multiple failed authentications
      - alert: BruteForceAttempt
        expr: |
          sum(rate(sergas_auth_failures_total[5m])) by (ip_address) > 5
        for: 2m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Possible brute force attack"
          description: "{{ $value }} failed auth attempts from {{ $labels.ip_address }}"

      # Unauthorized access attempts
      - alert: UnauthorizedAccessAttempts
        expr: |
          rate(sergas_authz_denials_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
          team: security
        annotations:
          summary: "High rate of authorization denials"
          description: "User {{ $labels.user_id }} attempted {{ $value }} unauthorized actions"

      # PII access spike
      - alert: UnusualPIIAccess
        expr: |
          rate(sergas_pii_access_total[1h]) > avg_over_time(sergas_pii_access_total[24h]) * 2
        for: 10m
        labels:
          severity: warning
          team: security
        annotations:
          summary: "Unusual PII access pattern"
          description: "PII access rate 2x higher than average"

      # Suspicious activity
      - alert: SuspiciousActivity
        expr: |
          sergas_suspicious_activity_total > 0
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Suspicious activity detected"
          description: "Type: {{ $labels.type }}, Severity: {{ $labels.severity }}"
```

---

## Incident Response

### Security Incident Playbook

#### 1. Detection Phase

**Indicators:**
- Alert from monitoring system
- Unusual activity in logs
- User report
- External notification

**Immediate Actions:**
```bash
# 1. Document incident
echo "Incident detected at $(date)" >> /var/log/incidents/$(date +%Y%m%d).log

# 2. Gather initial evidence
journalctl -u sergas-app --since "1 hour ago" > /tmp/incident-logs.txt
curl http://localhost:9090/api/v1/query?query=sergas_suspicious_activity_total > /tmp/incident-metrics.json

# 3. Alert security team
# Send notification via PagerDuty/Slack
```

#### 2. Containment Phase

**Actions:**
```bash
# Isolate affected systems
# For compromised user account
python scripts/disable_user.py --user-id USR-456

# Revoke all sessions
redis-cli --scan --pattern "session:user:USR-456:*" | xargs redis-cli del

# Block suspicious IP
sudo ufw deny from <IP_ADDRESS>

# Enable additional logging
export LOG_LEVEL=DEBUG
systemctl restart sergas-app
```

#### 3. Investigation Phase

**Evidence Collection:**
```bash
# Collect logs
mkdir -p /var/incidents/$(date +%Y%m%d)
journalctl -u sergas-app --since "24 hours ago" > /var/incidents/$(date +%Y%m%d)/app-logs.txt

# Database audit logs
psql -d sergas_prod -c "
COPY (SELECT * FROM audit_logs WHERE created_at > NOW() - INTERVAL '24 hours')
TO '/var/incidents/$(date +%Y%m%d)/audit-logs.csv' CSV HEADER;"

# Network traffic logs
tcpdump -i any -w /var/incidents/$(date +%Y%m%d)/traffic.pcap

# System state snapshot
ps aux > /var/incidents/$(date +%Y%m%d)/processes.txt
netstat -tunap > /var/incidents/$(date +%Y%m%d)/connections.txt
```

#### 4. Remediation Phase

**Actions:**
```bash
# Patch vulnerability
git pull origin security-patch
docker-compose up -d --build

# Reset compromised credentials
python scripts/rotate_secrets.py --force

# Update firewall rules
sudo ufw allow from <TRUSTED_IP> to any port 22
sudo ufw deny from <MALICIOUS_IP>

# Restore from clean backup if needed
bash scripts/restore-from-backup.sh <backup-file>
```

#### 5. Recovery Phase

**Actions:**
```bash
# Verify system integrity
python scripts/verify_integrity.py

# Re-enable services
systemctl start sergas-app

# Monitor for further activity
tail -f /var/log/sergas/app.log | grep -i "suspicious\|error\|unauthorized"

# Notify stakeholders
python scripts/send_incident_report.py --incident-id INC-123
```

---

## Compliance

### GDPR Compliance

#### Right to Access (Article 15)

```python
# Export all user data
async def export_user_data(user_id: str) -> dict:
    """Export all data associated with a user."""
    return {
        "user": await db.users.find_one({"id": user_id}),
        "accounts": await db.accounts.find({"owner_id": user_id}).to_list(),
        "activities": await db.activities.find({"user_id": user_id}).to_list(),
        "recommendations": await db.recommendations.find({"created_by": user_id}).to_list(),
        "audit_logs": await db.audit_logs.find({"user_id": user_id}).to_list(),
    }
```

#### Right to Erasure (Article 17)

```python
# Delete user data
async def delete_user_data(user_id: str, reason: str):
    """Delete all data associated with a user (GDPR right to erasure)."""

    # Log deletion request
    await AuditLogger.log_action(
        user_id=user_id,
        action="data.deletion_requested",
        resource_type="user",
        resource_id=user_id,
        details={"reason": reason},
        ip_address="system"
    )

    # Anonymize data instead of hard delete (for audit trail)
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "email": f"deleted_{user_id}@anonymized.local",
                "name": "Deleted User",
                "deleted_at": datetime.utcnow(),
                "deletion_reason": reason
            }
        }
    )

    # Delete personal data
    await db.activities.delete_many({"user_id": user_id})
    await db.sessions.delete_many({"user_id": user_id})
```

### SOC 2 Controls

#### Access Control (CC6.1)

- Implement RBAC
- MFA for admin access
- Regular access reviews
- Automated provisioning/deprovisioning

#### Logging and Monitoring (CC7.2)

- Comprehensive audit logging
- Log retention (1 year minimum)
- Tamper-evident logs
- Real-time security monitoring

#### Change Management (CC8.1)

- All changes via pull requests
- Automated testing
- Approval requirements
- Rollback procedures

---

## Security Checklist

### Production Deployment Checklist

- [ ] All secrets stored in AWS Secrets Manager
- [ ] TLS 1.3 enabled, TLS 1.0/1.1 disabled
- [ ] OAuth 2.0 authentication configured
- [ ] RBAC policies implemented
- [ ] Rate limiting enabled (60 req/min)
- [ ] PII detection and masking active
- [ ] Audit logging enabled
- [ ] Security headers configured (CSP, HSTS, X-Frame-Options)
- [ ] Database encryption at rest enabled
- [ ] Backup encryption enabled
- [ ] Firewall rules configured (only 80/443 exposed)
- [ ] DDoS protection active
- [ ] Security monitoring alerts configured
- [ ] Incident response plan documented
- [ ] Security training completed for team

### Monthly Security Review

- [ ] Review audit logs for anomalies
- [ ] Check for failed authentication attempts
- [ ] Review user access permissions
- [ ] Update dependencies (security patches)
- [ ] Rotate secrets and credentials
- [ ] Review firewall rules
- [ ] Test backup restoration
- [ ] Verify encryption is working
- [ ] Review security alerts and incidents
- [ ] Update security documentation

---

**Last Updated**: 2025-10-19
**Version**: 1.0.0
**Maintained by**: Sergas Security Team
