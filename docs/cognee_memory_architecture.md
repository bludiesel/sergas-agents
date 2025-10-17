# Cognee Memory Architecture Design

## 1. Executive Summary

This document defines the architecture for integrating Cognee as the persistent memory and knowledge management system for Sergas Super Account Manager agents. Cognee provides a self-hosted knowledge graph and vector store that enables agents to build contextual understanding of accounts, relationships, and historical interactions across sessions.

**Key Design Principles:**
- **Self-Hosted Deployment**: Full control over data, privacy, and scaling
- **Incremental Learning**: Continuous ingestion without full reprocessing
- **Semantic Search**: Vector embeddings for contextual account retrieval
- **Knowledge Graph**: Relationship mapping between accounts, contacts, deals, and activities
- **Session Persistence**: Cross-session memory for agent continuity
- **Real-Time Sync**: Near-real-time updates from Zoho CRM via webhooks

---

## 2. Cognee Architecture Overview

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Agent SDK Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Research    │  │   Account    │  │ Recommendation│         │
│  │   Agent      │  │   Manager    │  │    Engine     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │     Cognee MCP Wrapper               │
          │  - Query translation                 │
          │  - Result formatting                 │
          │  - Permission enforcement            │
          └──────────┬───────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │   Cognee SDK Client  │
          │  - API client        │
          │  - Connection pool   │
          │  - Retry logic       │
          └──────────┬───────────┘
                     │
     ┌───────────────┴───────────────┐
     │                               │
┌────▼─────────────┐      ┌─────────▼────────┐
│ Cognee Engine    │      │  Ingestion       │
│ - Query executor │      │  Pipeline        │
│ - Graph traversal│      │  - Zoho sync     │
│ - Vector search  │      │  - Webhooks      │
└────┬─────────────┘      └─────────┬────────┘
     │                               │
     └───────────────┬───────────────┘
                     │
     ┌───────────────▼───────────────┐
     │                               │
┌────▼──────────┐         ┌─────────▼────────┐
│  PostgreSQL   │         │   Qdrant         │
│  (Graph DB)   │         │   (Vector Store) │
└───────────────┘         └──────────────────┘
```

### 2.2 Deployment Architecture

**Self-Hosted Infrastructure:**
```
┌────────────────────────────────────────────────────┐
│              Kubernetes Cluster                     │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │       Cognee Service (3 replicas)        │     │
│  │  ┌────────────┐  ┌────────────┐         │     │
│  │  │ Cognee API │  │ Cognee API │  ...    │     │
│  │  └──────┬─────┘  └──────┬─────┘         │     │
│  └─────────┼────────────────┼───────────────┘     │
│            │                │                      │
│  ┌─────────▼────────────────▼───────────────┐     │
│  │       PostgreSQL (Primary + Replica)     │     │
│  │  - Knowledge graph storage               │     │
│  │  - Entity relationships                  │     │
│  │  - Metadata & audit logs                 │     │
│  └──────────────────────────────────────────┘     │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │       Qdrant (Vector DB Cluster)         │     │
│  │  - Embedding storage (1536-dim)          │     │
│  │  - Semantic search                       │     │
│  │  - Sharded for scale                     │     │
│  └──────────────────────────────────────────┘     │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │       Redis (Cache & Queue)              │     │
│  │  - Query result cache                    │     │
│  │  - Ingestion job queue                   │     │
│  └──────────────────────────────────────────┘     │
│                                                     │
│  ┌──────────────────────────────────────────┐     │
│  │       Ingestion Workers (5 replicas)     │     │
│  │  - Zoho data sync                        │     │
│  │  - Embedding generation                  │     │
│  │  - Graph updates                         │     │
│  └──────────────────────────────────────────┘     │
└────────────────────────────────────────────────────┘
```

---

## 3. Knowledge Graph Schema

### 3.1 Entity Types

**Core Entities:**
```typescript
enum EntityType {
  ACCOUNT = 'account',
  CONTACT = 'contact',
  DEAL = 'deal',
  NOTE = 'note',
  ACTIVITY = 'activity',
  TASK = 'task',
  EVENT = 'event',
  CALL = 'call',
  EMAIL = 'email',
  MEETING = 'meeting',
  OWNER = 'owner',
  PRODUCT = 'product',
  OPPORTUNITY = 'opportunity'
}

interface Entity {
  id: string;                  // Unique identifier
  type: EntityType;            // Entity classification
  sourceId: string;            // Zoho CRM record ID
  sourceSystem: 'zoho' | 'manual' | 'agent';
  name: string;                // Display name
  properties: Record<string, any>; // Dynamic properties
  embedding?: number[];        // Vector representation
  createdAt: Date;
  updatedAt: Date;
  lastSyncedAt: Date;
}
```

**Entity Schemas:**

```typescript
// Account Entity
interface AccountEntity extends Entity {
  type: EntityType.ACCOUNT;
  properties: {
    accountName: string;
    industry?: string;
    annualRevenue?: number;
    numberOfEmployees?: number;
    website?: string;
    phone?: string;
    billingAddress?: Address;
    accountOwner?: string;
    accountType?: 'Customer' | 'Prospect' | 'Partner';
    accountStatus?: 'Active' | 'Inactive' | 'Churned';
    healthScore?: number; // 0-100
    riskLevel?: 'Low' | 'Medium' | 'High';
    lastContactDate?: Date;
    contractEndDate?: Date;
    lifetimeValue?: number;
  };
}

// Contact Entity
interface ContactEntity extends Entity {
  type: EntityType.CONTACT;
  properties: {
    firstName: string;
    lastName: string;
    email: string;
    phone?: string;
    title?: string;
    department?: string;
    isPrimaryContact?: boolean;
    linkedInUrl?: string;
    lastEngagementDate?: Date;
    engagementScore?: number;
  };
}

// Deal Entity
interface DealEntity extends Entity {
  type: EntityType.DEAL;
  properties: {
    dealName: string;
    amount: number;
    stage: string;
    probability?: number;
    expectedCloseDate?: Date;
    actualCloseDate?: Date;
    dealOwner?: string;
    lostReason?: string;
    nextSteps?: string;
    competitorInfo?: string;
  };
}

// Note Entity
interface NoteEntity extends Entity {
  type: EntityType.NOTE;
  properties: {
    title?: string;
    content: string;
    author: string;
    noteType?: 'call_summary' | 'meeting_notes' | 'general' | 'internal';
    sentiment?: 'positive' | 'neutral' | 'negative';
    keyTopics?: string[];
  };
}

// Activity Entity
interface ActivityEntity extends Entity {
  type: EntityType.ACTIVITY | EntityType.TASK | EntityType.EVENT | EntityType.CALL;
  properties: {
    subject: string;
    description?: string;
    status: 'Not Started' | 'In Progress' | 'Completed' | 'Cancelled';
    priority?: 'Low' | 'Medium' | 'High';
    dueDate?: Date;
    completedDate?: Date;
    activityType?: string;
    duration?: number; // minutes
    outcome?: string;
  };
}
```

### 3.2 Relationship Types

**Core Relationships:**
```typescript
enum RelationshipType {
  // Account relationships
  HAS_CONTACT = 'has_contact',
  OWNS_DEAL = 'owns_deal',
  PARENT_OF = 'parent_of',
  PARTNER_WITH = 'partner_with',
  COMPETITOR_TO = 'competitor_to',

  // Contact relationships
  WORKS_AT = 'works_at',
  REPORTS_TO = 'reports_to',
  INFLUENCES = 'influences',

  // Deal relationships
  ASSOCIATED_WITH = 'associated_with',
  DEPENDS_ON = 'depends_on',
  FOLLOWS = 'follows',

  // Activity relationships
  RELATED_TO = 'related_to',
  MENTIONS = 'mentions',
  RESULTED_IN = 'resulted_in',

  // Ownership
  OWNED_BY = 'owned_by',
  ASSIGNED_TO = 'assigned_to'
}

interface Relationship {
  id: string;
  type: RelationshipType;
  sourceEntityId: string;
  targetEntityId: string;
  properties?: Record<string, any>;
  strength?: number; // 0.0 - 1.0 (for weighted relationships)
  createdAt: Date;
  updatedAt: Date;
}
```

**Relationship Examples:**
```typescript
// Account → Contact
{
  type: RelationshipType.HAS_CONTACT,
  sourceEntityId: 'account-123',
  targetEntityId: 'contact-456',
  properties: {
    isPrimary: true,
    role: 'Decision Maker'
  },
  strength: 1.0
}

// Contact → Contact (reporting structure)
{
  type: RelationshipType.REPORTS_TO,
  sourceEntityId: 'contact-456',
  targetEntityId: 'contact-789',
  properties: {
    relationship: 'Direct Report'
  }
}

// Deal → Account
{
  type: RelationshipType.ASSOCIATED_WITH,
  sourceEntityId: 'deal-321',
  targetEntityId: 'account-123',
  properties: {
    dealStage: 'Negotiation',
    probability: 0.75
  }
}

// Note → Account (mentions)
{
  type: RelationshipType.MENTIONS,
  sourceEntityId: 'note-555',
  targetEntityId: 'account-123',
  properties: {
    sentiment: 'positive',
    relevance: 0.85
  }
}
```

### 3.3 Graph Visualization

```
        ┌────────────┐
        │  Account   │
        │  "Acme Co" │
        └─────┬──────┘
              │
    ┌─────────┴─────────┬──────────────┐
    │                   │              │
    │ has_contact       │ owns_deal    │ has_note
    │                   │              │
┌───▼────┐         ┌────▼─────┐   ┌───▼────┐
│Contact │         │   Deal   │   │  Note  │
│"John"  │────────▶│ "$100K"  │   │"Risk"  │
└────────┘reports_to└──────────┘   └────────┘
    │
    │ assigned_to
    │
┌───▼────┐
│ Task   │
│"Follow │
│  up"   │
└────────┘
```

---

## 4. Ingestion Pipeline

### 4.1 Data Flow Architecture

```
┌─────────────┐
│  Zoho CRM   │
└──────┬──────┘
       │
       │ 1. Webhook (change event)
       │
┌──────▼──────────┐
│  Webhook        │
│  Handler        │
└──────┬──────────┘
       │
       │ 2. Enqueue job
       │
┌──────▼──────────┐
│  Redis Queue    │
│  (Bull/BullMQ)  │
└──────┬──────────┘
       │
       │ 3. Consume job
       │
┌──────▼──────────┐
│  Ingestion      │
│  Worker         │
│  1. Fetch full  │
│  2. Transform   │
│  3. Embed       │
│  4. Upsert      │
└──────┬──────────┘
       │
       ├──────────────────────┐
       │                      │
┌──────▼──────────┐   ┌───────▼─────────┐
│  PostgreSQL     │   │    Qdrant       │
│  (Graph Store)  │   │  (Vector Store) │
└─────────────────┘   └─────────────────┘
```

### 4.2 Ingestion Worker Implementation

**Worker Process:**
```typescript
import { cognee } from 'cognee';
import { Worker } from 'bullmq';

interface IngestionJob {
  module: string;        // 'Accounts', 'Contacts', etc.
  recordId: string;      // Zoho record ID
  operation: 'create' | 'update' | 'delete';
  timestamp: Date;
}

const ingestionWorker = new Worker('zoho-ingestion', async (job) => {
  const { module, recordId, operation } = job.data as IngestionJob;

  try {
    // 1. Fetch full record from Zoho
    const record = await zohoClient.getRecord(module, recordId);

    // 2. Transform to Cognee entity
    const entity = transformZohoToEntity(module, record);

    // 3. Generate embeddings
    const embedding = await generateEmbedding(entity);
    entity.embedding = embedding;

    // 4. Upsert to Cognee
    if (operation === 'delete') {
      await cognee.delete(entity.id);
    } else {
      await cognee.add(entity);

      // 5. Extract and create relationships
      const relationships = extractRelationships(module, record);
      for (const rel of relationships) {
        await cognee.addRelationship(rel);
      }
    }

    // 6. Update sync status
    await markSynced(module, recordId);

    metrics.increment('cognee.ingestion.success', { module });
  } catch (error) {
    metrics.increment('cognee.ingestion.error', { module });
    throw error; // Retry via Bull
  }
}, {
  connection: redisConnection,
  concurrency: 5
});
```

**Data Transformation:**
```typescript
function transformZohoToEntity(module: string, record: any): Entity {
  const entityType = moduleToEntityType(module);

  return {
    id: `${entityType}-${record.id}`,
    type: entityType,
    sourceId: record.id,
    sourceSystem: 'zoho',
    name: record[getNameField(module)],
    properties: extractProperties(module, record),
    createdAt: new Date(record.Created_Time),
    updatedAt: new Date(record.Modified_Time),
    lastSyncedAt: new Date()
  };
}

function extractProperties(module: string, record: any): Record<string, any> {
  const fieldMapping = FIELD_MAPPINGS[module];
  const properties = {};

  for (const [zohoField, cogneeProp] of Object.entries(fieldMapping)) {
    if (record[zohoField] !== undefined && record[zohoField] !== null) {
      properties[cogneeProp] = transformValue(record[zohoField]);
    }
  }

  return properties;
}

const FIELD_MAPPINGS = {
  Accounts: {
    'Account_Name': 'accountName',
    'Industry': 'industry',
    'Annual_Revenue': 'annualRevenue',
    'Employees': 'numberOfEmployees',
    'Website': 'website',
    'Phone': 'phone',
    'Account_Type': 'accountType',
    'Owner': 'accountOwner'
  },
  Contacts: {
    'First_Name': 'firstName',
    'Last_Name': 'lastName',
    'Email': 'email',
    'Phone': 'phone',
    'Title': 'title',
    'Department': 'department'
  },
  Deals: {
    'Deal_Name': 'dealName',
    'Amount': 'amount',
    'Stage': 'stage',
    'Probability': 'probability',
    'Closing_Date': 'expectedCloseDate',
    'Owner': 'dealOwner'
  }
  // ... additional modules
};
```

**Relationship Extraction:**
```typescript
function extractRelationships(module: string, record: any): Relationship[] {
  const relationships: Relationship[] = [];
  const sourceEntityId = `${moduleToEntityType(module)}-${record.id}`;

  // Extract ownership relationships
  if (record.Owner?.id) {
    relationships.push({
      id: `${sourceEntityId}-owned-by-${record.Owner.id}`,
      type: RelationshipType.OWNED_BY,
      sourceEntityId,
      targetEntityId: `owner-${record.Owner.id}`,
      createdAt: new Date(),
      updatedAt: new Date()
    });
  }

  // Extract parent relationships (Accounts)
  if (module === 'Accounts' && record.Parent_Account?.id) {
    relationships.push({
      id: `${sourceEntityId}-child-of-${record.Parent_Account.id}`,
      type: RelationshipType.PARENT_OF,
      sourceEntityId: `account-${record.Parent_Account.id}`,
      targetEntityId: sourceEntityId,
      createdAt: new Date(),
      updatedAt: new Date()
    });
  }

  // Extract contact-account relationships
  if (module === 'Contacts' && record.Account_Name?.id) {
    relationships.push({
      id: `${record.Account_Name.id}-has-contact-${record.id}`,
      type: RelationshipType.HAS_CONTACT,
      sourceEntityId: `account-${record.Account_Name.id}`,
      targetEntityId: sourceEntityId,
      properties: {
        isPrimary: record.Primary_Contact || false
      },
      createdAt: new Date(),
      updatedAt: new Date()
    });
  }

  // Extract deal-account relationships
  if (module === 'Deals' && record.Account_Name?.id) {
    relationships.push({
      id: `${record.Account_Name.id}-owns-deal-${record.id}`,
      type: RelationshipType.OWNS_DEAL,
      sourceEntityId: `account-${record.Account_Name.id}`,
      targetEntityId: sourceEntityId,
      properties: {
        stage: record.Stage,
        probability: record.Probability
      },
      strength: (record.Probability || 0) / 100,
      createdAt: new Date(),
      updatedAt: new Date()
    });
  }

  return relationships;
}
```

### 4.3 Incremental Update Strategy

**Change Detection:**
```typescript
class IncrementalSyncManager {
  private lastSyncTimestamp: Map<string, Date> = new Map();

  async syncModule(module: string): Promise<void> {
    const lastSync = this.lastSyncTimestamp.get(module) || new Date(0);

    // Fetch only modified records since last sync
    const modifiedRecords = await zohoClient.searchRecords(module, {
      criteria: `(Modified_Time:greater_than:${lastSync.toISOString()})`
    });

    // Queue ingestion jobs
    for (const record of modifiedRecords) {
      await ingestionQueue.add('ingest', {
        module,
        recordId: record.id,
        operation: 'update',
        timestamp: new Date()
      });
    }

    this.lastSyncTimestamp.set(module, new Date());
    await this.persistCheckpoint(module, new Date());
  }

  async persistCheckpoint(module: string, timestamp: Date): Promise<void> {
    await cognee.setMetadata(`sync_checkpoint:${module}`, {
      lastSyncedAt: timestamp,
      recordCount: await cognee.count({ type: moduleToEntityType(module) })
    });
  }
}
```

**Deduplication:**
```typescript
async function upsertEntity(entity: Entity): Promise<void> {
  // Check if entity exists
  const existing = await cognee.get(entity.id);

  if (existing) {
    // Compare timestamps to prevent stale updates
    if (entity.updatedAt > existing.updatedAt) {
      await cognee.update(entity.id, entity);
      metrics.increment('cognee.entity.updated');
    } else {
      metrics.increment('cognee.entity.skipped_stale');
    }
  } else {
    await cognee.create(entity);
    metrics.increment('cognee.entity.created');
  }
}
```

### 4.4 Embedding Generation

**Text Extraction for Embeddings:**
```typescript
function extractTextForEmbedding(entity: Entity): string {
  const parts: string[] = [];

  // Include entity name
  parts.push(entity.name);

  // Include key properties based on entity type
  switch (entity.type) {
    case EntityType.ACCOUNT:
      const account = entity as AccountEntity;
      parts.push(account.properties.industry || '');
      parts.push(account.properties.accountType || '');
      parts.push(`Revenue: ${account.properties.annualRevenue || 'N/A'}`);
      break;

    case EntityType.CONTACT:
      const contact = entity as ContactEntity;
      parts.push(contact.properties.title || '');
      parts.push(contact.properties.department || '');
      break;

    case EntityType.NOTE:
      const note = entity as NoteEntity;
      parts.push(note.properties.title || '');
      parts.push(note.properties.content);
      break;

    case EntityType.DEAL:
      const deal = entity as DealEntity;
      parts.push(deal.properties.stage);
      parts.push(`Amount: ${deal.properties.amount}`);
      parts.push(deal.properties.nextSteps || '');
      break;
  }

  return parts.filter(p => p.length > 0).join(' | ');
}

async function generateEmbedding(entity: Entity): Promise<number[]> {
  const text = extractTextForEmbedding(entity);

  // Use OpenAI Ada-002 or similar embedding model
  const response = await openai.embeddings.create({
    model: 'text-embedding-ada-002',
    input: text
  });

  return response.data[0].embedding;
}
```

---

## 5. Query Patterns for Agent Access

### 5.1 Common Query Types

**1. Account Context Retrieval:**
```typescript
async function getAccountContext(accountId: string): Promise<AccountContext> {
  // Fetch account entity
  const account = await cognee.get(`account-${accountId}`);

  // Fetch related entities via graph traversal
  const contacts = await cognee.traverse({
    startNode: account.id,
    relationshipType: RelationshipType.HAS_CONTACT,
    depth: 1
  });

  const deals = await cognee.traverse({
    startNode: account.id,
    relationshipType: RelationshipType.OWNS_DEAL,
    depth: 1
  });

  const recentNotes = await cognee.traverse({
    startNode: account.id,
    relationshipType: RelationshipType.MENTIONS,
    depth: 1,
    filters: {
      createdAt: { $gte: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000) } // Last 90 days
    },
    orderBy: { createdAt: 'desc' },
    limit: 10
  });

  const openActivities = await cognee.traverse({
    startNode: account.id,
    relationshipType: RelationshipType.RELATED_TO,
    depth: 1,
    filters: {
      type: { $in: [EntityType.TASK, EntityType.EVENT] },
      'properties.status': { $ne: 'Completed' }
    }
  });

  return {
    account,
    contacts,
    deals,
    recentNotes,
    openActivities
  };
}
```

**2. Semantic Search:**
```typescript
async function semanticSearch(query: string, options?: SearchOptions): Promise<Entity[]> {
  // Generate query embedding
  const queryEmbedding = await generateEmbedding({
    id: 'temp',
    type: EntityType.ACCOUNT,
    name: query,
    properties: {},
    sourceId: '',
    sourceSystem: 'manual',
    createdAt: new Date(),
    updatedAt: new Date(),
    lastSyncedAt: new Date()
  });

  // Vector similarity search in Qdrant
  const results = await cognee.vectorSearch({
    embedding: queryEmbedding,
    limit: options?.limit || 10,
    threshold: options?.threshold || 0.7,
    filters: options?.filters
  });

  return results;
}

// Example usage
const atRiskAccounts = await semanticSearch(
  'accounts with declining engagement and upcoming contract renewals',
  {
    filters: { type: EntityType.ACCOUNT },
    limit: 20
  }
);
```

**3. Relationship Traversal:**
```typescript
async function findInfluencers(accountId: string): Promise<ContactEntity[]> {
  // Find contacts at account
  const contacts = await cognee.traverse({
    startNode: `account-${accountId}`,
    relationshipType: RelationshipType.HAS_CONTACT,
    depth: 1
  });

  // Find who they influence (outbound relationships)
  const influencers = [];
  for (const contact of contacts) {
    const influenced = await cognee.traverse({
      startNode: contact.id,
      relationshipType: RelationshipType.INFLUENCES,
      depth: 2 // Multi-hop: contact → influences → influences
    });

    if (influenced.length >= 3) {
      influencers.push(contact);
    }
  }

  return influencers;
}
```

**4. Temporal Queries:**
```typescript
async function getAccountTimeline(
  accountId: string,
  startDate: Date,
  endDate: Date
): Promise<TimelineEvent[]> {
  // Fetch all entities related to account within date range
  const events = await cognee.query({
    traverse: {
      startNode: `account-${accountId}`,
      relationshipTypes: [
        RelationshipType.MENTIONS,
        RelationshipType.RELATED_TO,
        RelationshipType.RESULTED_IN
      ],
      depth: 2
    },
    filters: {
      createdAt: {
        $gte: startDate,
        $lte: endDate
      }
    },
    orderBy: { createdAt: 'asc' }
  });

  return events.map(e => ({
    date: e.createdAt,
    type: e.type,
    description: generateEventDescription(e),
    entity: e
  }));
}
```

**5. Aggregate Queries:**
```typescript
async function calculateAccountHealth(accountId: string): Promise<HealthScore> {
  const context = await getAccountContext(accountId);

  // Engagement score (based on recent activities)
  const engagementScore = context.recentNotes.length * 10 +
                          context.openActivities.length * 5;

  // Deal pipeline score
  const pipelineScore = context.deals
    .filter(d => d.properties.stage !== 'Closed Lost')
    .reduce((sum, d) => sum + (d.properties.probability || 0), 0);

  // Contact coverage score
  const contactScore = context.contacts.length >= 3 ? 100 :
                       context.contacts.length * 33;

  // Sentiment analysis on notes
  const sentimentScore = await analyzeSentiment(context.recentNotes);

  const overallHealth = (
    engagementScore * 0.3 +
    pipelineScore * 0.3 +
    contactScore * 0.2 +
    sentimentScore * 0.2
  );

  return {
    overall: Math.min(100, overallHealth),
    engagement: engagementScore,
    pipeline: pipelineScore,
    contacts: contactScore,
    sentiment: sentimentScore,
    riskLevel: overallHealth < 40 ? 'High' :
               overallHealth < 70 ? 'Medium' : 'Low'
  };
}
```

### 5.2 Query Optimization

**Caching Strategy:**
```typescript
class CogneeQueryCache {
  private cache: Redis;
  private ttl: number = 300; // 5 minutes default

  async get<T>(key: string): Promise<T | null> {
    const cached = await this.cache.get(key);
    if (cached) {
      metrics.increment('cognee.cache.hit');
      return JSON.parse(cached);
    }
    metrics.increment('cognee.cache.miss');
    return null;
  }

  async set<T>(key: string, value: T, ttl?: number): Promise<void> {
    await this.cache.setex(
      key,
      ttl || this.ttl,
      JSON.stringify(value)
    );
  }

  async invalidate(pattern: string): Promise<void> {
    const keys = await this.cache.keys(pattern);
    if (keys.length > 0) {
      await this.cache.del(...keys);
    }
  }
}

// Usage
async function getCachedAccountContext(accountId: string): Promise<AccountContext> {
  const cacheKey = `account_context:${accountId}`;

  let context = await queryCache.get<AccountContext>(cacheKey);
  if (!context) {
    context = await getAccountContext(accountId);
    await queryCache.set(cacheKey, context, 300);
  }

  return context;
}
```

**Index Optimization:**
```sql
-- PostgreSQL indexes for graph queries
CREATE INDEX idx_entity_type ON entities(type);
CREATE INDEX idx_entity_source ON entities(source_system, source_id);
CREATE INDEX idx_entity_updated ON entities(updated_at);

CREATE INDEX idx_relationship_type ON relationships(type);
CREATE INDEX idx_relationship_source ON relationships(source_entity_id);
CREATE INDEX idx_relationship_target ON relationships(target_entity_id);
CREATE INDEX idx_relationship_composite ON relationships(type, source_entity_id, target_entity_id);

-- Qdrant collection configuration
{
  "vector_size": 1536,
  "distance": "Cosine",
  "hnsw_config": {
    "m": 16,
    "ef_construct": 200
  },
  "optimizers_config": {
    "default_segment_number": 5
  }
}
```

---

## 6. MCP Wrapper for Cognee SDK

### 6.1 MCP Server Implementation

**MCP Tool Definitions:**
```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { cognee } from 'cognee';

const server = new Server({
  name: 'cognee-memory',
  version: '1.0.0'
}, {
  capabilities: {
    tools: {}
  }
});

// Tool: Get account context
server.setRequestHandler('tools/call', async (request) => {
  if (request.params.name === 'get_account_context') {
    const { accountId } = request.params.arguments;
    const context = await getAccountContext(accountId);

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(context, null, 2)
      }]
    };
  }

  if (request.params.name === 'semantic_search') {
    const { query, limit, filters } = request.params.arguments;
    const results = await semanticSearch(query, { limit, filters });

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(results, null, 2)
      }]
    };
  }

  if (request.params.name === 'calculate_account_health') {
    const { accountId } = request.params.arguments;
    const health = await calculateAccountHealth(accountId);

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(health, null, 2)
      }]
    };
  }

  throw new Error(`Unknown tool: ${request.params.name}`);
});

// Tool listing
server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'get_account_context',
        description: 'Retrieve comprehensive context for an account including contacts, deals, notes, and activities',
        inputSchema: {
          type: 'object',
          properties: {
            accountId: { type: 'string', description: 'Zoho CRM Account ID' }
          },
          required: ['accountId']
        }
      },
      {
        name: 'semantic_search',
        description: 'Search for entities using natural language queries with semantic understanding',
        inputSchema: {
          type: 'object',
          properties: {
            query: { type: 'string', description: 'Natural language search query' },
            limit: { type: 'number', description: 'Maximum results to return', default: 10 },
            filters: { type: 'object', description: 'Additional filters (entity type, date range, etc.)' }
          },
          required: ['query']
        }
      },
      {
        name: 'calculate_account_health',
        description: 'Calculate health score for an account based on engagement, pipeline, and sentiment',
        inputSchema: {
          type: 'object',
          properties: {
            accountId: { type: 'string', description: 'Zoho CRM Account ID' }
          },
          required: ['accountId']
        }
      },
      {
        name: 'get_account_timeline',
        description: 'Retrieve chronological timeline of events for an account',
        inputSchema: {
          type: 'object',
          properties: {
            accountId: { type: 'string' },
            startDate: { type: 'string', format: 'date-time' },
            endDate: { type: 'string', format: 'date-time' }
          },
          required: ['accountId', 'startDate', 'endDate']
        }
      },
      {
        name: 'find_similar_accounts',
        description: 'Find accounts similar to a given account based on properties and behavior',
        inputSchema: {
          type: 'object',
          properties: {
            accountId: { type: 'string' },
            limit: { type: 'number', default: 5 }
          },
          required: ['accountId']
        }
      }
    ]
  };
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

### 6.2 MCP Configuration

**Claude Desktop Configuration:**
```json
{
  "mcpServers": {
    "cognee-memory": {
      "command": "node",
      "args": [
        "/path/to/sergas_agents/mcp/cognee-server.js"
      ],
      "env": {
        "COGNEE_API_URL": "http://localhost:8000",
        "COGNEE_API_KEY": "${VAULT_COGNEE_API_KEY}",
        "REDIS_URL": "redis://localhost:6379"
      }
    }
  }
}
```

---

## 7. Data Retention and Deduplication

### 7.1 Retention Policies

**Time-Based Retention:**
```typescript
interface RetentionPolicy {
  entityType: EntityType;
  retentionDays: number;
  archiveBeforeDelete: boolean;
}

const RETENTION_POLICIES: RetentionPolicy[] = [
  { entityType: EntityType.ACCOUNT, retentionDays: -1, archiveBeforeDelete: false }, // Permanent
  { entityType: EntityType.CONTACT, retentionDays: -1, archiveBeforeDelete: false }, // Permanent
  { entityType: EntityType.DEAL, retentionDays: 1825, archiveBeforeDelete: true },   // 5 years
  { entityType: EntityType.NOTE, retentionDays: 730, archiveBeforeDelete: true },    // 2 years
  { entityType: EntityType.ACTIVITY, retentionDays: 365, archiveBeforeDelete: false }, // 1 year
  { entityType: EntityType.EMAIL, retentionDays: 365, archiveBeforeDelete: true }    // 1 year
];

async function applyRetentionPolicies(): Promise<void> {
  for (const policy of RETENTION_POLICIES) {
    if (policy.retentionDays === -1) continue; // Skip permanent retention

    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - policy.retentionDays);

    const expiredEntities = await cognee.query({
      filters: {
        type: policy.entityType,
        createdAt: { $lt: cutoffDate }
      }
    });

    for (const entity of expiredEntities) {
      if (policy.archiveBeforeDelete) {
        await archiveEntity(entity);
      }
      await cognee.delete(entity.id);
      metrics.increment('cognee.retention.deleted', { type: policy.entityType });
    }
  }
}
```

### 7.2 Deduplication Strategy

**Duplicate Detection:**
```typescript
async function detectDuplicates(entity: Entity): Promise<Entity[]> {
  // Strategy 1: Exact source ID match
  const exactMatches = await cognee.query({
    filters: {
      sourceSystem: entity.sourceSystem,
      sourceId: entity.sourceId,
      id: { $ne: entity.id } // Exclude self
    }
  });

  if (exactMatches.length > 0) {
    return exactMatches;
  }

  // Strategy 2: Fuzzy name matching + property similarity
  const candidates = await cognee.query({
    filters: {
      type: entity.type,
      name: { $regex: fuzzyMatch(entity.name) }
    }
  });

  const duplicates = candidates.filter(candidate => {
    const similarity = calculateSimilarity(entity, candidate);
    return similarity > 0.85; // 85% similarity threshold
  });

  return duplicates;
}

function calculateSimilarity(entity1: Entity, entity2: Entity): number {
  // Name similarity (Levenshtein distance)
  const nameSimilarity = 1 - (levenshteinDistance(entity1.name, entity2.name) /
                               Math.max(entity1.name.length, entity2.name.length));

  // Property similarity
  const props1 = Object.entries(entity1.properties);
  const props2 = Object.entries(entity2.properties);
  const matchingProps = props1.filter(([key, val]) =>
    entity2.properties[key] === val
  ).length;
  const propSimilarity = matchingProps / Math.max(props1.length, props2.length);

  // Weighted average
  return nameSimilarity * 0.6 + propSimilarity * 0.4;
}

async function mergeDuplicates(primary: Entity, duplicate: Entity): Promise<void> {
  // 1. Merge properties (prefer non-null values)
  const mergedProperties = { ...duplicate.properties, ...primary.properties };

  // 2. Transfer relationships from duplicate to primary
  const duplicateRelationships = await cognee.getRelationships(duplicate.id);
  for (const rel of duplicateRelationships) {
    if (rel.sourceEntityId === duplicate.id) {
      rel.sourceEntityId = primary.id;
    }
    if (rel.targetEntityId === duplicate.id) {
      rel.targetEntityId = primary.id;
    }
    await cognee.upsertRelationship(rel);
  }

  // 3. Update primary entity
  await cognee.update(primary.id, { properties: mergedProperties });

  // 4. Delete duplicate
  await cognee.delete(duplicate.id);

  metrics.increment('cognee.deduplication.merged');
}
```

---

## 8. Performance Optimization

### 8.1 Read Optimization

**Connection Pooling:**
```typescript
import { Pool } from 'pg';
import { QdrantClient } from '@qdrant/js-client-rest';

const pgPool = new Pool({
  host: 'postgres.cognee.internal',
  port: 5432,
  database: 'cognee',
  user: 'cognee',
  password: await secrets.get('POSTGRES_PASSWORD'),
  max: 20, // Max connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000
});

const qdrantClient = new QdrantClient({
  url: 'http://qdrant.cognee.internal:6333',
  apiKey: await secrets.get('QDRANT_API_KEY')
});
```

**Query Result Caching:**
```typescript
class CogneeClient {
  private cache: Redis;

  async query<T>(query: Query): Promise<T[]> {
    const cacheKey = this.generateCacheKey(query);

    // Try cache first
    const cached = await this.cache.get(cacheKey);
    if (cached) {
      return JSON.parse(cached);
    }

    // Execute query
    const results = await this.executeQuery<T>(query);

    // Cache results (TTL based on query type)
    const ttl = this.getCacheTTL(query);
    await this.cache.setex(cacheKey, ttl, JSON.stringify(results));

    return results;
  }

  private getCacheTTL(query: Query): number {
    // Static data (accounts, contacts) - 5 minutes
    if (query.filters?.type === EntityType.ACCOUNT ||
        query.filters?.type === EntityType.CONTACT) {
      return 300;
    }

    // Dynamic data (activities, notes) - 1 minute
    return 60;
  }
}
```

### 8.2 Write Optimization

**Batch Ingestion:**
```typescript
class BatchIngestionManager {
  private batch: Entity[] = [];
  private batchSize = 100;
  private flushInterval = 5000; // 5 seconds

  async add(entity: Entity): Promise<void> {
    this.batch.push(entity);

    if (this.batch.length >= this.batchSize) {
      await this.flush();
    }
  }

  async flush(): Promise<void> {
    if (this.batch.length === 0) return;

    const entitiesToInsert = [...this.batch];
    this.batch = [];

    // Bulk insert to PostgreSQL
    await pgPool.query(
      `INSERT INTO entities (id, type, source_id, source_system, name, properties, embedding, created_at, updated_at)
       VALUES ${entitiesToInsert.map((_, i) =>
         `($${i*9+1}, $${i*9+2}, $${i*9+3}, $${i*9+4}, $${i*9+5}, $${i*9+6}, $${i*9+7}, $${i*9+8}, $${i*9+9})`
       ).join(', ')}
       ON CONFLICT (id) DO UPDATE SET
         properties = EXCLUDED.properties,
         embedding = EXCLUDED.embedding,
         updated_at = EXCLUDED.updated_at`,
      entitiesToInsert.flatMap(e => [
        e.id, e.type, e.sourceId, e.sourceSystem, e.name,
        JSON.stringify(e.properties), e.embedding, e.createdAt, e.updatedAt
      ])
    );

    // Bulk upsert to Qdrant
    await qdrantClient.upsert('entities', {
      wait: false,
      points: entitiesToInsert.map(e => ({
        id: e.id,
        vector: e.embedding,
        payload: {
          type: e.type,
          name: e.name,
          sourceSystem: e.sourceSystem
        }
      }))
    });

    metrics.increment('cognee.batch.flushed', { size: entitiesToInsert.length });
  }
}
```

---

## 9. Monitoring and Observability

### 9.1 Key Metrics

**Ingestion Metrics:**
```typescript
// Throughput
metrics.histogram('cognee.ingestion.duration', durationMs, { module });
metrics.increment('cognee.ingestion.records', { module, operation });

// Queue metrics
metrics.gauge('cognee.ingestion.queue.size', queueSize);
metrics.gauge('cognee.ingestion.queue.lag', lagSeconds);

// Error metrics
metrics.increment('cognee.ingestion.error', { module, errorType });
```

**Query Metrics:**
```typescript
// Performance
metrics.histogram('cognee.query.duration', durationMs, { queryType });
metrics.histogram('cognee.query.result_size', resultCount);

// Cache performance
metrics.increment('cognee.cache.hit' | 'cognee.cache.miss', { queryType });
metrics.gauge('cognee.cache.hit_rate', hitRate);
```

**Storage Metrics:**
```typescript
// Database metrics
metrics.gauge('cognee.postgres.connections', connectionCount);
metrics.gauge('cognee.postgres.entity_count', entityCount);
metrics.gauge('cognee.postgres.relationship_count', relationshipCount);

// Vector store metrics
metrics.gauge('cognee.qdrant.collection_size', vectorCount);
metrics.histogram('cognee.qdrant.search_duration', durationMs);
```

### 9.2 Health Checks

**Cognee Health Endpoint:**
```typescript
app.get('/health/cognee', async (req, res) => {
  const checks = {
    postgres: await checkPostgresHealth(),
    qdrant: await checkQdrantHealth(),
    redis: await checkRedisHealth(),
    ingestionQueue: await checkQueueHealth()
  };

  const healthy = Object.values(checks).every(c => c.status === 'ok');

  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'healthy' : 'degraded',
    checks,
    stats: {
      totalEntities: await cognee.count(),
      recentIngestions: await getRecentIngestionCount(),
      cacheHitRate: await getCacheHitRate()
    }
  });
});
```

---

## 10. Disaster Recovery

### 10.1 Backup Strategy

**PostgreSQL Backups:**
```bash
# Automated daily backups
0 2 * * * pg_dump -h postgres.cognee.internal -U cognee cognee | \
          gzip > /backups/cognee-$(date +\%Y\%m\%d).sql.gz

# Retention: 7 daily, 4 weekly, 12 monthly
```

**Qdrant Snapshots:**
```typescript
async function createQdrantSnapshot(): Promise<void> {
  const snapshot = await qdrantClient.createSnapshot('entities');

  // Upload to S3
  await s3Client.upload({
    Bucket: 'cognee-backups',
    Key: `qdrant/entities-${Date.now()}.snapshot`,
    Body: snapshot
  });
}
```

### 10.2 Recovery Procedures

**Full Restore:**
```bash
# 1. Restore PostgreSQL
gunzip < /backups/cognee-20251018.sql.gz | \
  psql -h postgres.cognee.internal -U cognee cognee

# 2. Restore Qdrant
aws s3 cp s3://cognee-backups/qdrant/entities-latest.snapshot /tmp/
curl -X POST 'http://qdrant.cognee.internal:6333/collections/entities/snapshots/recover' \
  --data-binary @/tmp/entities-latest.snapshot

# 3. Rebuild cache
npm run cognee:rebuild-cache
```

---

## 11. Future Enhancements

1. **Multi-Tenancy**: Isolate knowledge graphs per customer
2. **Federated Learning**: Train embeddings on combined datasets without sharing raw data
3. **Graph Analytics**: PageRank for contact influence, community detection for account clustering
4. **Streaming Updates**: Real-time graph updates via change data capture (CDC)
5. **Advanced NLP**: Entity extraction from unstructured notes, sentiment analysis

---

## 12. References

- Cognee Documentation: https://cognee.ai/docs
- PostgreSQL Graph Extensions: https://age.apache.org/
- Qdrant Vector Database: https://qdrant.tech/documentation/
- OpenAI Embeddings: https://platform.openai.com/docs/guides/embeddings

---

**Document Version**: 1.0
**Last Updated**: 2025-10-18
**Author**: System Architecture Designer
**Status**: Final
