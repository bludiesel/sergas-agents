# Secrets Management Strategy

## 1. Executive Summary

This document defines the comprehensive secrets management strategy for the Sergas Super Account Manager system. Proper secrets management is critical for securing OAuth tokens, API keys, database credentials, and other sensitive configuration data across the integration stack (Zoho CRM, Cognee, MCP servers, Claude agents).

**Key Design Principles:**
- **Zero-Trust Architecture**: Never store secrets in code, configuration files, or environment variables in plain text
- **Least Privilege Access**: Grant minimal necessary permissions to services and users
- **Secret Rotation**: Automated periodic rotation with zero-downtime transitions
- **Audit and Compliance**: Complete audit trail of secret access and modifications
- **Multi-Environment Isolation**: Separate secrets per environment (dev, staging, production)
- **Encryption at Rest and in Transit**: All secrets encrypted with industry-standard algorithms

---

## 2. Secrets Inventory

### 2.1 Categorization

**Tier 1 - Critical Secrets (High Risk):**
- Zoho CRM OAuth refresh tokens
- PostgreSQL database credentials (Cognee)
- AWS IAM access keys (infrastructure)
- Encryption master keys
- Production API keys

**Tier 2 - Sensitive Secrets (Medium Risk):**
- Zoho CRM client ID and secret
- Qdrant API keys
- Redis connection passwords
- MCP server authentication tokens
- Webhook authentication secrets

**Tier 3 - Operational Secrets (Lower Risk):**
- Development/staging API keys
- Internal service tokens
- Monitoring/logging credentials
- Non-production database passwords

### 2.2 Secret Types by Component

| Component | Secret Type | Rotation Frequency | Storage Location |
|-----------|-------------|-------------------|------------------|
| Zoho CRM | OAuth refresh token | On-demand (if compromised) | AWS Secrets Manager |
| Zoho CRM | Client ID/Secret | Annually | AWS Secrets Manager |
| Cognee | PostgreSQL password | 90 days | AWS Secrets Manager |
| Cognee | Qdrant API key | 90 days | AWS Secrets Manager |
| MCP | Authentication tokens | 30 days | AWS Secrets Manager |
| Redis | Connection password | 90 days | AWS Secrets Manager |
| OpenAI | API key | 90 days | AWS Secrets Manager |
| Webhook | Bearer tokens | 30 days | AWS Secrets Manager |
| Encryption | Master key | Never (backup only) | AWS KMS |

---

## 3. Secrets Storage Solution

### 3.1 Primary Solution: AWS Secrets Manager

**Selection Rationale:**
- Native AWS integration (Lambda, ECS, RDS)
- Automatic secret rotation support
- Fine-grained IAM access control
- Encryption at rest with AWS KMS
- Audit logging via CloudTrail
- High availability (multi-AZ)
- Pay-per-secret pricing model

**Architecture:**
```
┌──────────────────────────────────────────────┐
│         Application Layer                     │
│  ┌────────────┐  ┌────────────┐             │
│  │   Agent    │  │  Cognee    │             │
│  │   Host     │  │  Service   │             │
│  └─────┬──────┘  └─────┬──────┘             │
└────────┼────────────────┼────────────────────┘
         │                │
         │ 1. Request secret
         │                │
┌────────▼────────────────▼────────────────────┐
│      AWS Secrets Manager                      │
│  ┌────────────────────────────────────────┐  │
│  │  Secrets Store                         │  │
│  │  - zoho/oauth/refresh_token            │  │
│  │  - cognee/postgres/password            │  │
│  │  - redis/connection_string             │  │
│  │  - openai/api_key                      │  │
│  └────────────────┬───────────────────────┘  │
└───────────────────┼──────────────────────────┘
                    │
                    │ 2. Decrypt with KMS
                    │
┌───────────────────▼──────────────────────────┐
│         AWS KMS (Key Management)              │
│  - Master encryption keys                     │
│  - Automatic key rotation                     │
└───────────────────────────────────────────────┘
```

### 3.2 Alternative Solution: HashiCorp Vault

**When to Consider Vault:**
- Multi-cloud deployment (AWS + GCP + Azure)
- Advanced dynamic secrets (generate on-demand)
- Complex secret templating requirements
- Existing Vault infrastructure

**Comparison Matrix:**

| Feature | AWS Secrets Manager | HashiCorp Vault |
|---------|---------------------|-----------------|
| Setup Complexity | Low (managed service) | High (self-hosted) |
| AWS Integration | Native | Via API |
| Dynamic Secrets | Limited | Extensive |
| Cost | $0.40/secret/month + API calls | Infrastructure + licensing |
| High Availability | Built-in (99.99% SLA) | Manual setup |
| Secret Rotation | Built-in for RDS, Lambda | Manual scripting |
| Audit Logging | CloudTrail (native) | External integration |
| **Recommendation** | **Primary choice** | Alternative for multi-cloud |

---

## 4. Secret Lifecycle Management

### 4.1 Secret Creation

**Creation Process:**
```typescript
import { SecretsManagerClient, CreateSecretCommand } from '@aws-sdk/client-secrets-manager';

async function createSecret(
  name: string,
  value: string,
  description: string,
  tags: Record<string, string>
): Promise<string> {
  const client = new SecretsManagerClient({ region: 'us-west-2' });

  const command = new CreateSecretCommand({
    Name: name,
    Description: description,
    SecretString: value,
    KmsKeyId: 'alias/sergas-secrets', // Custom KMS key
    Tags: [
      ...Object.entries(tags).map(([Key, Value]) => ({ Key, Value })),
      { Key: 'ManagedBy', Value: 'sergas-agents' },
      { Key: 'CreatedAt', Value: new Date().toISOString() }
    ]
  });

  const response = await client.send(command);

  // Log creation event
  await auditLog.write({
    event: 'secret_created',
    secretName: name,
    arn: response.ARN,
    timestamp: new Date()
  });

  return response.ARN;
}

// Example usage
await createSecret(
  'sergas/zoho/oauth/refresh_token',
  refreshToken,
  'Zoho CRM OAuth refresh token for production',
  {
    Environment: 'production',
    Component: 'zoho-crm',
    RotationEnabled: 'false',
    Tier: 'critical'
  }
);
```

**Naming Convention:**
```
{organization}/{component}/{environment}/{secret_type}

Examples:
- sergas/zoho/prod/refresh_token
- sergas/cognee/prod/postgres_password
- sergas/redis/prod/connection_string
- sergas/mcp/prod/auth_token
- sergas/openai/prod/api_key
```

### 4.2 Secret Retrieval

**Secure Access Pattern:**
```typescript
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

class SecretManager {
  private client: SecretsManagerClient;
  private cache: Map<string, { value: string; expiresAt: Date }> = new Map();
  private cacheTTL = 300000; // 5 minutes

  constructor() {
    this.client = new SecretsManagerClient({
      region: process.env.AWS_REGION || 'us-west-2'
    });
  }

  async get(secretName: string): Promise<string> {
    // Check cache first
    const cached = this.cache.get(secretName);
    if (cached && cached.expiresAt > new Date()) {
      metrics.increment('secrets.cache.hit', { secret: secretName });
      return cached.value;
    }

    // Retrieve from Secrets Manager
    try {
      const command = new GetSecretValueCommand({
        SecretId: secretName,
        VersionStage: 'AWSCURRENT' // Always get latest version
      });

      const response = await this.client.send(command);
      const value = response.SecretString || '';

      // Cache the value
      this.cache.set(secretName, {
        value,
        expiresAt: new Date(Date.now() + this.cacheTTL)
      });

      metrics.increment('secrets.retrieved', { secret: secretName });
      return value;
    } catch (error) {
      metrics.increment('secrets.error', { secret: secretName, error: error.name });
      throw new SecretRetrievalError(`Failed to retrieve secret: ${secretName}`, error);
    }
  }

  async getJSON<T>(secretName: string): Promise<T> {
    const value = await this.get(secretName);
    return JSON.parse(value);
  }

  // Invalidate cache entry (e.g., after rotation)
  invalidate(secretName: string): void {
    this.cache.delete(secretName);
  }

  // Clear all cached secrets
  clearCache(): void {
    this.cache.clear();
  }
}

// Singleton instance
export const secretManager = new SecretManager();
```

**Usage Examples:**
```typescript
// Simple string secret
const apiKey = await secretManager.get('sergas/openai/prod/api_key');

// JSON secret (database credentials)
const dbCreds = await secretManager.getJSON<{
  host: string;
  port: number;
  username: string;
  password: string;
}>('sergas/cognee/prod/postgres_credentials');

// OAuth token structure
const oauthTokens = await secretManager.getJSON<{
  access_token: string;
  refresh_token: string;
  expires_at: string;
}>('sergas/zoho/prod/oauth_tokens');
```

### 4.3 Secret Rotation

**Automatic Rotation Strategy:**

**For RDS/PostgreSQL (Built-in Rotation):**
```typescript
import { RotateSecretCommand } from '@aws-sdk/client-secrets-manager';

async function enableAutomaticRotation(secretName: string): Promise<void> {
  const client = new SecretsManagerClient({ region: 'us-west-2' });

  await client.send(new RotateSecretCommand({
    SecretId: secretName,
    RotationLambdaARN: 'arn:aws:lambda:us-west-2:123456789012:function:SecretsManagerRDSPostgreSQLRotation',
    RotationRules: {
      AutomaticallyAfterDays: 90 // Rotate every 90 days
    }
  }));
}
```

**For Custom Secrets (OAuth Tokens, API Keys):**
```typescript
// Lambda function for OAuth token rotation
export async function rotateZohoOAuthToken(event: RotationEvent): Promise<void> {
  const secretId = event.SecretId;
  const token = event.Token;
  const step = event.Step;

  switch (step) {
    case 'createSecret':
      // Generate new access token using refresh token
      const currentSecret = await secretsManager.getSecretValue({ SecretId: secretId });
      const { refresh_token } = JSON.parse(currentSecret.SecretString);

      const newTokens = await zohoClient.refreshAccessToken(refresh_token);

      // Store new token with AWSPENDING label
      await secretsManager.putSecretValue({
        SecretId: secretId,
        ClientRequestToken: token,
        SecretString: JSON.stringify(newTokens),
        VersionStages: ['AWSPENDING']
      });
      break;

    case 'setSecret':
      // Test new token
      const pendingSecret = await secretsManager.getSecretValue({
        SecretId: secretId,
        VersionStage: 'AWSPENDING'
      });

      const testTokens = JSON.parse(pendingSecret.SecretString);
      await testZohoConnection(testTokens.access_token);
      break;

    case 'testSecret':
      // No additional testing needed (already done in setSecret)
      break;

    case 'finishSecret':
      // Move AWSCURRENT label to new version
      await secretsManager.updateSecretVersionStage({
        SecretId: secretId,
        VersionStage: 'AWSCURRENT',
        MoveToVersionId: token,
        RemoveFromVersionId: event.PreviousVersionId
      });

      // Invalidate cache
      secretManager.invalidate(secretId);

      // Audit log
      await auditLog.write({
        event: 'secret_rotated',
        secretId,
        newVersion: token,
        timestamp: new Date()
      });
      break;
  }
}
```

**Manual Rotation (Emergency):**
```typescript
async function emergencyRotateSecret(secretName: string, newValue: string): Promise<void> {
  const client = new SecretsManagerClient({ region: 'us-west-2' });

  // Update secret value
  await client.send(new PutSecretValueCommand({
    SecretId: secretName,
    SecretString: newValue
  }));

  // Invalidate cache
  secretManager.invalidate(secretName);

  // Alert operations team
  await notifyOps(`Emergency rotation performed for secret: ${secretName}`);

  // Audit log
  await auditLog.write({
    event: 'emergency_rotation',
    secretName,
    initiator: 'manual',
    timestamp: new Date()
  });
}
```

### 4.4 Secret Deletion

**Soft Deletion with Recovery Window:**
```typescript
import { DeleteSecretCommand } from '@aws-sdk/client-secrets-manager';

async function deleteSecret(
  secretName: string,
  recoveryWindowDays: number = 30
): Promise<void> {
  const client = new SecretsManagerClient({ region: 'us-west-2' });

  await client.send(new DeleteSecretCommand({
    SecretId: secretName,
    RecoveryWindowInDays: recoveryWindowDays,
    ForceDeleteWithoutRecovery: false // Safety: require recovery window
  }));

  // Audit log
  await auditLog.write({
    event: 'secret_deleted',
    secretName,
    recoveryWindowDays,
    deletionDate: new Date(Date.now() + recoveryWindowDays * 24 * 60 * 60 * 1000),
    timestamp: new Date()
  });
}
```

---

## 5. Access Control and Permissions

### 5.1 IAM Policy Design

**Least Privilege Policy (Agent Hosts):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReadZohoSecrets",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-west-2:123456789012:secret:sergas/zoho/prod/*"
      ],
      "Condition": {
        "StringEquals": {
          "secretsmanager:VersionStage": "AWSCURRENT"
        }
      }
    },
    {
      "Sid": "AllowKMSDecryption",
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey"
      ],
      "Resource": "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
    }
  ]
}
```

**Admin Policy (Rotation Lambda):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecretVersionStage"
      ],
      "Resource": "arn:aws:secretsmanager:us-west-2:123456789012:secret:sergas/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetRandomPassword"
      ],
      "Resource": "*"
    }
  ]
}
```

**Deny Policy (Prevent Deletion):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": [
        "secretsmanager:DeleteSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-west-2:123456789012:secret:sergas/*/prod/*"
      ],
      "Condition": {
        "StringNotEquals": {
          "aws:PrincipalArn": [
            "arn:aws:iam::123456789012:role/SerGasAdmin"
          ]
        }
      }
    }
  ]
}
```

### 5.2 Role-Based Access

**Service Roles:**

| Role | Services | Permissions | Secrets Access |
|------|----------|-------------|----------------|
| `SerGasAgentHost` | ECS tasks, EC2 instances | Read-only | Zoho, Cognee, Redis, OpenAI |
| `SerGasCogneeWorker` | ECS tasks | Read-only | Cognee DB, Redis, OpenAI |
| `SerGasRotationLambda` | Lambda functions | Read-write (rotation) | All secrets |
| `SerGasDevOps` | CI/CD, administrators | Full access | All secrets (with audit) |
| `SerGasMonitoring` | CloudWatch, logging | Read metadata only | None (only metadata) |

**IAM Role Assignment:**
```typescript
// ECS Task Definition
{
  "taskRoleArn": "arn:aws:iam::123456789012:role/SerGasAgentHost",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "agent-host",
      "image": "sergas/agent-host:latest",
      "secrets": [
        {
          "name": "ZOHO_REFRESH_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:sergas/zoho/prod/refresh_token"
        },
        {
          "name": "COGNEE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:sergas/cognee/prod/api_key"
        }
      ]
    }
  ]
}
```

### 5.3 Multi-Factor Authentication (MFA)

**Require MFA for Admin Operations:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": [
        "secretsmanager:PutSecretValue",
        "secretsmanager:UpdateSecret",
        "secretsmanager:DeleteSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-west-2:123456789012:secret:sergas/*/prod/*",
      "Condition": {
        "BoolIfExists": {
          "aws:MultiFactorAuthPresent": "false"
        }
      }
    }
  ]
}
```

---

## 6. Environment-Specific Configurations

### 6.1 Environment Separation

**Secret Namespaces:**
```
Production:
  sergas/zoho/prod/*
  sergas/cognee/prod/*
  sergas/redis/prod/*

Staging:
  sergas/zoho/staging/*
  sergas/cognee/staging/*
  sergas/redis/staging/*

Development:
  sergas/zoho/dev/*
  sergas/cognee/dev/*
  sergas/redis/dev/*
```

**Environment Detection:**
```typescript
class EnvironmentConfig {
  private environment: 'dev' | 'staging' | 'prod';

  constructor() {
    this.environment = (process.env.ENVIRONMENT as any) || 'dev';
  }

  getSecretName(component: string, secretType: string): string {
    return `sergas/${component}/${this.environment}/${secretType}`;
  }

  async getZohoRefreshToken(): Promise<string> {
    return secretManager.get(
      this.getSecretName('zoho', 'refresh_token')
    );
  }

  async getCogneeDBCredentials(): Promise<DBCredentials> {
    return secretManager.getJSON(
      this.getSecretName('cognee', 'postgres_credentials')
    );
  }
}

export const config = new EnvironmentConfig();
```

### 6.2 Configuration Templates

**Secret Templates (JSON Structure):**
```json
// Zoho OAuth Tokens
{
  "access_token": "1000.abcd1234...",
  "refresh_token": "1000.wxyz5678...",
  "expires_at": "2025-10-18T22:00:00Z",
  "token_type": "Bearer",
  "api_domain": "https://www.zohoapis.com"
}

// Database Credentials
{
  "host": "postgres.cognee.internal",
  "port": 5432,
  "database": "cognee",
  "username": "cognee_app",
  "password": "random-generated-password",
  "ssl_mode": "require"
}

// Redis Connection
{
  "host": "redis.sergas.internal",
  "port": 6379,
  "password": "random-generated-password",
  "db": 0,
  "tls": true
}

// MCP Authentication Token
{
  "token": "mcp_auth_token_...",
  "expires_at": "2025-11-18T00:00:00Z",
  "scopes": ["read", "write"],
  "issuer": "sergas-auth-service"
}
```

---

## 7. Audit Logging and Compliance

### 7.1 AWS CloudTrail Integration

**Logged Events:**
- Secret creation/deletion
- Secret value retrieval (who, when, from where)
- Secret rotation (successful/failed)
- Permission changes
- KMS key usage

**CloudTrail Query (Athena):**
```sql
SELECT
  eventTime,
  userIdentity.principalId,
  sourceIPAddress,
  eventName,
  requestParameters.secretId,
  responseElements.ARN
FROM cloudtrail_logs
WHERE eventSource = 'secretsmanager.amazonaws.com'
  AND eventName IN ('GetSecretValue', 'PutSecretValue', 'DeleteSecret')
  AND requestParameters.secretId LIKE '%sergas/zoho/prod%'
ORDER BY eventTime DESC
LIMIT 100;
```

### 7.2 Custom Audit Logging

**Application-Level Audit Trail:**
```typescript
interface SecretAuditLog {
  timestamp: Date;
  event: 'retrieved' | 'rotated' | 'created' | 'deleted' | 'access_denied';
  secretName: string;
  userId?: string;
  serviceRole: string;
  ipAddress?: string;
  success: boolean;
  errorMessage?: string;
}

class AuditLogger {
  async logSecretAccess(log: SecretAuditLog): Promise<void> {
    // Write to dedicated audit log table
    await auditDB.insert('secret_audit_logs', log);

    // Send to SIEM (Security Information and Event Management)
    await siemClient.send({
      timestamp: log.timestamp,
      severity: log.success ? 'INFO' : 'WARNING',
      category: 'secrets_access',
      data: log
    });

    // Alert on suspicious patterns
    if (!log.success || this.isSuspicious(log)) {
      await alertOps('Suspicious secret access detected', log);
    }
  }

  private isSuspicious(log: SecretAuditLog): boolean {
    // Check for unusual access patterns
    const recentAccess = await this.getRecentAccess(log.secretName, 60);

    // Alert if >10 accesses in 1 minute
    if (recentAccess.length > 10) {
      return true;
    }

    // Alert if access from unexpected IP
    const knownIPs = await this.getKnownIPs(log.serviceRole);
    if (log.ipAddress && !knownIPs.includes(log.ipAddress)) {
      return true;
    }

    return false;
  }
}

export const auditLogger = new AuditLogger();
```

### 7.3 Compliance Requirements

**SOC 2 Compliance Checklist:**
- ✅ Secrets encrypted at rest (AWS KMS)
- ✅ Secrets encrypted in transit (TLS 1.2+)
- ✅ Access logging (CloudTrail + custom audit logs)
- ✅ Least privilege access (IAM policies)
- ✅ Secret rotation (automated)
- ✅ MFA for admin operations
- ✅ Audit trail retention (7 years)

**GDPR Compliance:**
- ✅ Data residency (secrets stored in specific AWS region)
- ✅ Right to erasure (secret deletion with recovery window)
- ✅ Access logs (who accessed which secrets)
- ✅ Encryption standards (AES-256)

---

## 8. Disaster Recovery

### 8.1 Backup Strategy

**AWS Secrets Manager Backup:**
```typescript
async function backupAllSecrets(): Promise<void> {
  const client = new SecretsManagerClient({ region: 'us-west-2' });

  // List all secrets
  const secrets = await client.send(new ListSecretsCommand({}));

  const backup = {
    timestamp: new Date(),
    region: 'us-west-2',
    secrets: []
  };

  for (const secret of secrets.SecretList) {
    // Note: Only metadata is backed up, not secret values (security)
    backup.secrets.push({
      name: secret.Name,
      arn: secret.ARN,
      description: secret.Description,
      rotationEnabled: secret.RotationEnabled,
      tags: secret.Tags
    });
  }

  // Store backup metadata
  await s3Client.putObject({
    Bucket: 'sergas-secrets-backups',
    Key: `backups/secrets-metadata-${Date.now()}.json`,
    Body: JSON.stringify(backup, null, 2),
    ServerSideEncryption: 'aws:kms',
    SSEKMSKeyId: 'alias/sergas-secrets'
  });
}
```

### 8.2 Recovery Procedures

**Secret Recovery from Deletion:**
```typescript
import { RestoreSecretCommand } from '@aws-sdk/client-secrets-manager';

async function recoverDeletedSecret(secretName: string): Promise<void> {
  const client = new SecretsManagerClient({ region: 'us-west-2' });

  await client.send(new RestoreSecretCommand({
    SecretId: secretName
  }));

  await auditLog.write({
    event: 'secret_restored',
    secretName,
    timestamp: new Date()
  });
}
```

**Emergency Access Procedure:**
```markdown
1. Verify identity (MFA required)
2. Log incident ticket
3. Use break-glass IAM role:
   aws sts assume-role --role-arn arn:aws:iam::123456789012:role/SerGasEmergencyAccess
4. Retrieve secret:
   aws secretsmanager get-secret-value --secret-id sergas/zoho/prod/refresh_token
5. Document access in audit log
6. Rotate secret after emergency resolved
```

---

## 9. Monitoring and Alerting

### 9.1 Key Metrics

**CloudWatch Metrics:**
```typescript
// Secret retrieval latency
metrics.histogram('secrets.retrieval.duration', durationMs, { secret: secretName });

// Retrieval errors
metrics.increment('secrets.retrieval.error', {
  secret: secretName,
  errorType: error.name
});

// Cache hit rate
metrics.gauge('secrets.cache.hit_rate', hitRate);

// Rotation status
metrics.gauge('secrets.rotation.days_since_last', daysSinceRotation, {
  secret: secretName
});
```

### 9.2 Alerting Rules

**Critical Alerts:**
```yaml
# Secret retrieval failure spike
- alert: SecretRetrievalFailureSpike
  expr: rate(secrets_retrieval_error_total[5m]) > 0.1
  for: 2m
  severity: critical
  annotations:
    summary: "High rate of secret retrieval failures"
    description: "{{ $value }} failures per second in the last 5 minutes"

# Secret rotation overdue
- alert: SecretRotationOverdue
  expr: secrets_rotation_days_since_last > 100
  for: 1h
  severity: warning
  annotations:
    summary: "Secret rotation is overdue"
    description: "Secret {{ $labels.secret }} has not been rotated in {{ $value }} days"

# Unauthorized access attempts
- alert: UnauthorizedSecretAccess
  expr: increase(secrets_access_denied_total[10m]) > 5
  for: 5m
  severity: critical
  annotations:
    summary: "Multiple unauthorized secret access attempts detected"
    description: "{{ $value }} access denied events in the last 10 minutes"
```

---

## 10. Best Practices and Guidelines

### 10.1 Development Guidelines

**DO:**
- ✅ Use `secretManager.get()` for all secret retrieval
- ✅ Cache secrets in memory with short TTL (5 minutes)
- ✅ Use environment variables only to store secret ARNs/names
- ✅ Validate secret format after retrieval
- ✅ Clear secrets from memory after use (for sensitive operations)
- ✅ Use least privilege IAM roles
- ✅ Rotate secrets regularly
- ✅ Log secret access for audit trail

**DON'T:**
- ❌ Store secrets in environment variables directly
- ❌ Hardcode secrets in source code
- ❌ Commit secrets to version control
- ❌ Log secret values (log secret names only)
- ❌ Share secrets via email/chat
- ❌ Use the same secret across environments
- ❌ Disable secret rotation
- ❌ Grant wildcard permissions (`secretsmanager:*`)

### 10.2 Code Review Checklist

**Pre-Commit Checks:**
```bash
# Run pre-commit hook to detect secrets
git-secrets --scan

# Check for potential secrets in code
trufflehog filesystem . --json

# Validate IAM policies
cfn-policy-validator validate --template-path iam-policies.json
```

**Review Questions:**
- [ ] Are all secrets retrieved via SecretManager?
- [ ] Are secrets cached with appropriate TTL?
- [ ] Are error messages sanitized (no secret leakage)?
- [ ] Are IAM policies using least privilege?
- [ ] Is MFA required for production secret access?
- [ ] Are audit logs written for secret operations?

---

## 11. Migration Plan

### 11.1 Migration from Environment Variables

**Step 1: Create Secrets in AWS Secrets Manager**
```bash
# Migrate Zoho OAuth tokens
aws secretsmanager create-secret \
  --name sergas/zoho/prod/refresh_token \
  --secret-string "$ZOHO_REFRESH_TOKEN" \
  --description "Zoho CRM OAuth refresh token"

# Migrate database credentials
aws secretsmanager create-secret \
  --name sergas/cognee/prod/postgres_credentials \
  --secret-string '{
    "host": "'"$DB_HOST"'",
    "username": "'"$DB_USER"'",
    "password": "'"$DB_PASSWORD"'"
  }'
```

**Step 2: Update Application Code**
```typescript
// BEFORE (environment variables)
const zohoToken = process.env.ZOHO_REFRESH_TOKEN;
const dbPassword = process.env.DB_PASSWORD;

// AFTER (Secrets Manager)
const zohoToken = await secretManager.get('sergas/zoho/prod/refresh_token');
const dbCreds = await secretManager.getJSON('sergas/cognee/prod/postgres_credentials');
```

**Step 3: Update IAM Roles**
```bash
# Grant ECS task role access to secrets
aws iam put-role-policy \
  --role-name SerGasAgentHost \
  --policy-name SecretsAccess \
  --policy-document file://secrets-policy.json
```

**Step 4: Deploy and Test**
```bash
# Deploy with new secret management
./deploy.sh --environment prod

# Verify secrets are retrieved correctly
./test-secrets.sh
```

**Step 5: Remove Environment Variables**
```bash
# Remove from ECS task definition
aws ecs register-task-definition \
  --family sergas-agent-host \
  --task-role-arn arn:aws:iam::123456789012:role/SerGasAgentHost \
  --container-definitions file://task-definition.json
  # (with secrets moved from "environment" to "secrets" section)
```

---

## 12. Troubleshooting Guide

### 12.1 Common Issues

**Issue: AccessDeniedException when retrieving secret**
```
Error: User: arn:aws:sts::123456789012:assumed-role/SerGasAgentHost/i-1234567890abcdef0
is not authorized to perform: secretsmanager:GetSecretValue on resource:
arn:aws:secretsmanager:us-west-2:123456789012:secret:sergas/zoho/prod/refresh_token
```

**Resolution:**
1. Verify IAM role has `secretsmanager:GetSecretValue` permission
2. Check secret ARN is correct
3. Ensure KMS key permissions allow decryption

**Issue: Secret rotation failure**
```
Error: Lambda function SecretsManagerRDSPostgreSQLRotation failed to execute
```

**Resolution:**
1. Check Lambda execution logs in CloudWatch
2. Verify Lambda has network access to database
3. Ensure Lambda IAM role has `secretsmanager:PutSecretValue` permission
4. Test database connectivity from Lambda VPC

**Issue: Cache inconsistency after rotation**
```
Error: Invalid OAuth token (401 Unauthorized)
```

**Resolution:**
```typescript
// Force cache invalidation after rotation
secretManager.invalidate('sergas/zoho/prod/refresh_token');

// Or clear all caches
secretManager.clearCache();
```

---

## 13. Cost Optimization

### 13.1 Pricing Model

**AWS Secrets Manager Costs:**
- $0.40 per secret per month
- $0.05 per 10,000 API calls

**Example Monthly Cost:**
```
Secrets (20 secrets × $0.40) = $8.00
API calls (1M calls × $0.05/10K) = $5.00
KMS encryption (included in Secrets Manager)
Total = ~$13/month
```

### 13.2 Cost Optimization Strategies

**Consolidate Related Secrets:**
```typescript
// BEFORE (3 secrets × $0.40 = $1.20/month)
await secretManager.get('sergas/cognee/prod/db_host');
await secretManager.get('sergas/cognee/prod/db_username');
await secretManager.get('sergas/cognee/prod/db_password');

// AFTER (1 secret × $0.40 = $0.40/month)
const dbCreds = await secretManager.getJSON('sergas/cognee/prod/postgres_credentials');
// { host, username, password }
```

**Implement Efficient Caching:**
```typescript
// Cache secrets for 5 minutes to reduce API calls
// 1 call per 5 minutes = 8,640 calls/month vs. 1 per request = 2.6M calls/month
const cached = await secretManager.get('sergas/openai/prod/api_key');
// Saves: (2.6M - 8.6K) × $0.05/10K = ~$13/month per frequently-accessed secret
```

---

## 14. References

- AWS Secrets Manager Documentation: https://docs.aws.amazon.com/secretsmanager/
- AWS KMS Best Practices: https://docs.aws.amazon.com/kms/latest/developerguide/best-practices.html
- IAM Best Practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- OWASP Secrets Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- HashiCorp Vault: https://www.vaultproject.io/docs

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Author**: System Architecture Designer
**Status**: Final
