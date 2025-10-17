# SPARC Pseudocode Phase
## Sergas Super Account Manager Agent - Algorithm Design

**Document Version**: 1.0
**Phase**: Pseudocode (SPARC Methodology)
**Author**: SPARC Pseudocode Agent
**Date**: 2025-10-18

---

## Table of Contents
1. [Overview](#overview)
2. [Core Data Structures](#core-data-structures)
3. [Main Orchestration Loop](#main-orchestration-loop)
4. [Zoho Data Scout Workflow](#zoho-data-scout-workflow)
5. [Memory Analyst Workflow](#memory-analyst-workflow)
6. [Recommendation Author Workflow](#recommendation-author-workflow)
7. [Approval Gate Mechanism](#approval-gate-mechanism)
8. [Error Handling & Retry Logic](#error-handling--retry-logic)
9. [Audit Trail Generation](#audit-trail-generation)
10. [Session State Management](#session-state-management)
11. [Performance Optimization Strategies](#performance-optimization-strategies)
12. [Complexity Analysis](#complexity-analysis)

---

## Overview

This document defines the algorithmic workflows for the Sergas Super Account Manager Agent, a multi-agent system coordinating three specialized subagents:
- **Zoho Data Scout**: Retrieves and filters account data from Zoho CRM
- **Memory Analyst**: Queries historical context and constructs timelines
- **Recommendation Author**: Synthesizes actionable recommendations with confidence scoring

### Design Principles
1. **Language Agnostic**: Pseudocode can be implemented in any language
2. **Modular Design**: Clear separation of concerns between agents
3. **Fault Tolerant**: Graceful degradation when services unavailable
4. **Auditable**: Complete trail of decisions and data sources
5. **Human-in-Loop**: Approval gates before any CRM modifications

---

## Core Data Structures

### Account Record
```
STRUCTURE: AccountRecord
    accountId: string (unique identifier)
    accountName: string
    ownerId: string
    ownerName: string
    status: enum {Active, Inactive, AtRisk, Closed}
    lastModified: timestamp
    lastActivityDate: timestamp
    dealCount: integer
    totalValue: currency
    customFields: Map<string, any>
    changeFlags: Set<ChangeType>
END STRUCTURE

ENUM: ChangeType
    OWNER_CHANGE
    STATUS_CHANGE
    DEAL_STALLED
    HIGH_VALUE_ACTIVITY
    INACTIVITY_THRESHOLD
    CONTACT_ADDED
    CUSTOM_FIELD_MODIFIED
END ENUM
```

### Historical Context
```
STRUCTURE: HistoricalContext
    accountId: string
    timeline: List<TimelineEvent>
    keyInsights: List<Insight>
    priorRecommendations: List<PastRecommendation>
    sentimentTrend: enum {Improving, Stable, Declining, Unknown}
    engagementScore: float (0.0-1.0)
END STRUCTURE

STRUCTURE: TimelineEvent
    timestamp: timestamp
    eventType: string
    description: string
    participants: List<string>
    outcome: string (optional)
    sourceReference: string
END STRUCTURE

STRUCTURE: Insight
    category: enum {Risk, Opportunity, Pattern, Commitment}
    description: string
    confidence: float (0.0-1.0)
    evidenceReferences: List<string>
    generatedAt: timestamp
END STRUCTURE
```

### Recommendation
```
STRUCTURE: Recommendation
    recommendationId: string (UUID)
    accountId: string
    ownerId: string
    priority: enum {Critical, High, Medium, Low}
    actionType: enum {FollowUp, Escalate, Schedule, Update, Monitor}
    title: string
    rationale: string
    suggestedActions: List<Action>
    confidence: float (0.0-1.0)
    supportingData: List<DataReference>
    generatedAt: timestamp
    expiresAt: timestamp (optional)
    status: enum {Pending, Approved, Rejected, Expired}
END STRUCTURE

STRUCTURE: Action
    actionId: string
    actionType: string
    description: string
    draftContent: string (optional - email/note draft)
    crmUpdates: Map<string, any> (optional)
    estimatedEffort: integer (minutes)
END STRUCTURE
```

### Session State
```
STRUCTURE: SessionState
    sessionId: string (UUID)
    runType: enum {Scheduled, OnDemand}
    startTime: timestamp
    status: enum {Running, Completed, Failed, PartialSuccess}
    accountsProcessed: integer
    accountsFailed: integer
    recommendations: List<Recommendation>
    errors: List<ErrorRecord>
    metrics: PerformanceMetrics
END STRUCTURE

STRUCTURE: PerformanceMetrics
    totalDuration: milliseconds
    apiCallCount: integer
    tokenUsage: integer
    cacheHitRate: float
    avgAccountProcessingTime: milliseconds
END STRUCTURE
```

### Queue Management
```
STRUCTURE: ProcessingQueue
    Type: Priority Queue (Min-Heap)
    Key: (priority, lastProcessed timestamp)
    Purpose: Fair scheduling of account reviews

    Operations:
        - enqueue(accountId, priority): O(log n)
        - dequeue(): O(log n)
        - peek(): O(1)
        - updatePriority(accountId, newPriority): O(log n)
END STRUCTURE

STRUCTURE: ResultCache
    Type: LRU Cache with TTL
    Size: 1000 entries
    TTL: 6 hours
    Purpose: Reduce redundant API calls

    Operations:
        - get(key): O(1)
        - set(key, value, ttl): O(1)
        - invalidate(pattern): O(n)
END STRUCTURE
```

---

## Main Orchestration Loop

### Algorithm: OrchestrationController

```
ALGORITHM: RunAccountReviewCycle
INPUT:
    runConfig (configuration object)
    accountFilter (optional filter criteria)
OUTPUT:
    sessionState (complete session results)

CONSTANTS:
    MAX_CONCURRENT_ACCOUNTS = 10
    MAX_RETRIES = 3
    BATCH_SIZE = 50
    TIMEOUT_PER_ACCOUNT = 30 seconds

BEGIN
    // Initialize session
    session ← CreateSession(runConfig)
    auditLog ← InitializeAuditLog(session.sessionId)

    LOG("Starting account review cycle", session.sessionId)

    // Phase 1: Account Discovery
    accounts ← DiscoverAccountsToProcess(accountFilter, runConfig)

    IF accounts is empty THEN
        LOG("No accounts to process")
        RETURN CompleteSession(session, "NO_WORK")
    END IF

    LOG("Discovered {count} accounts for processing", accounts.size)

    // Phase 2: Queue Management
    queue ← BuildProcessingQueue(accounts, runConfig.priorityRules)

    // Phase 3: Batch Processing with Concurrency
    WHILE NOT queue.isEmpty() DO
        batch ← DequeueAccounts(queue, BATCH_SIZE)

        results ← ProcessAccountBatch(
            batch,
            session,
            auditLog,
            MAX_CONCURRENT_ACCOUNTS
        )

        // Update session state
        FOR EACH result IN results DO
            IF result.success THEN
                session.accountsProcessed ← session.accountsProcessed + 1
                session.recommendations.append(result.recommendations)
            ELSE
                session.accountsFailed ← session.accountsFailed + 1
                session.errors.append(result.error)
            END IF
        END FOR

        // Circuit breaker: halt if error rate too high
        errorRate ← session.accountsFailed / (session.accountsProcessed + session.accountsFailed)
        IF errorRate > 0.3 THEN
            LOG("High error rate detected, halting cycle", errorRate)
            session.status ← Failed
            BREAK
        END IF

        // Rate limiting pause
        Sleep(calculateBackoff(results))

    END WHILE

    // Phase 4: Compile Owner Briefs
    ownerBriefs ← CompileOwnerBriefs(session.recommendations)

    // Phase 5: Generate Audit Trail
    auditReport ← GenerateAuditReport(session, auditLog)

    // Phase 6: Finalize Session
    session.status ← DetermineSessionStatus(session)
    PersistSession(session)

    LOG("Account review cycle complete", session.sessionId, session.status)

    RETURN session
END

SUBROUTINE: DiscoverAccountsToProcess
INPUT: accountFilter, runConfig
OUTPUT: List<AccountRecord>

BEGIN
    // Determine scope
    IF accountFilter is not null THEN
        scope ← accountFilter
    ELSE IF runConfig.runType == Scheduled THEN
        scope ← BuildScheduledScope(runConfig)
    ELSE
        scope ← BuildOnDemandScope(runConfig)
    END IF

    // Query Zoho for candidate accounts
    candidateAccounts ← []

    TRY
        rawAccounts ← ZohoDataScout.fetchAccounts(scope)

        // Apply business rules
        FOR EACH account IN rawAccounts DO
            IF ShouldProcessAccount(account, runConfig) THEN
                candidateAccounts.append(account)
            END IF
        END FOR

    CATCH error AS e
        LOG_ERROR("Failed to discover accounts", e)
        THROW OrchestratorException("Discovery phase failed", e)
    END TRY

    RETURN candidateAccounts
END

SUBROUTINE: BuildScheduledScope
INPUT: runConfig
OUTPUT: FilterCriteria

BEGIN
    criteria ← new FilterCriteria()

    // Time-based filtering
    IF runConfig.cadence == "daily" THEN
        criteria.modifiedSince ← CurrentTime() - 24 hours
    ELSE IF runConfig.cadence == "weekly" THEN
        criteria.modifiedSince ← CurrentTime() - 7 days
    END IF

    // Status filtering
    criteria.statuses ← ["Active", "AtRisk"]

    // Owner filtering (if configured)
    IF runConfig.ownerSegment is not null THEN
        criteria.ownerIds ← runConfig.ownerSegment
    END IF

    RETURN criteria
END

SUBROUTINE: BuildProcessingQueue
INPUT: accounts (List<AccountRecord>), priorityRules
OUTPUT: ProcessingQueue

BEGIN
    queue ← new ProcessingQueue()

    FOR EACH account IN accounts DO
        priority ← CalculateAccountPriority(account, priorityRules)
        queue.enqueue(account.accountId, priority)
    END FOR

    RETURN queue
END

SUBROUTINE: CalculateAccountPriority
INPUT: account, priorityRules
OUTPUT: integer (priority score, lower = higher priority)

BEGIN
    score ← 100  // Base priority

    // Critical flags increase priority (lower score)
    IF account.changeFlags.contains(OWNER_CHANGE) THEN
        score ← score - 50
    END IF

    IF account.changeFlags.contains(DEAL_STALLED) THEN
        score ← score - 40
    END IF

    IF account.changeFlags.contains(INACTIVITY_THRESHOLD) THEN
        score ← score - 30
    END IF

    // High value accounts increase priority
    IF account.totalValue > priorityRules.highValueThreshold THEN
        score ← score - 20
    END IF

    // Apply custom rules
    FOR EACH rule IN priorityRules.customRules DO
        IF rule.matches(account) THEN
            score ← score + rule.adjustment
        END IF
    END FOR

    RETURN MAX(0, score)
END

SUBROUTINE: ProcessAccountBatch
INPUT: batch, session, auditLog, maxConcurrent
OUTPUT: List<ProcessingResult>

BEGIN
    results ← []
    semaphore ← new Semaphore(maxConcurrent)

    // Parallel processing with concurrency limit
    tasks ← []
    FOR EACH accountId IN batch DO
        task ← ASYNC ProcessSingleAccount(
            accountId,
            session,
            auditLog,
            semaphore
        )
        tasks.append(task)
    END FOR

    // Wait for all tasks to complete
    results ← AWAIT_ALL(tasks)

    RETURN results
END

SUBROUTINE: ProcessSingleAccount
INPUT: accountId, session, auditLog, semaphore
OUTPUT: ProcessingResult

BEGIN
    semaphore.acquire()
    startTime ← CurrentTime()

    TRY
        // Phase 1: Data Scout retrieves current state
        accountData ← ZohoDataScout.fetchAccountDetails(accountId)
        LOG_AUDIT(auditLog, "DATA_FETCH", accountId, accountData)

        // Phase 2: Memory Analyst retrieves context
        historicalContext ← MemoryAnalyst.analyzeAccountHistory(accountId)
        LOG_AUDIT(auditLog, "CONTEXT_RETRIEVAL", accountId, historicalContext)

        // Phase 3: Recommendation Author synthesizes recommendations
        recommendations ← RecommendationAuthor.generateRecommendations(
            accountData,
            historicalContext,
            session.runConfig
        )
        LOG_AUDIT(auditLog, "RECOMMENDATIONS", accountId, recommendations)

        duration ← CurrentTime() - startTime

        RETURN ProcessingResult(
            success: true,
            accountId: accountId,
            recommendations: recommendations,
            processingTime: duration
        )

    CATCH error AS e
        LOG_ERROR("Failed to process account", accountId, e)
        LOG_AUDIT(auditLog, "ERROR", accountId, e)

        RETURN ProcessingResult(
            success: false,
            accountId: accountId,
            error: ErrorRecord(accountId, e, CurrentTime())
        )

    FINALLY
        semaphore.release()
    END TRY
END

SUBROUTINE: CompileOwnerBriefs
INPUT: recommendations (List<Recommendation>)
OUTPUT: Map<ownerId, OwnerBrief>

BEGIN
    briefsByOwner ← new Map()

    // Group recommendations by owner
    FOR EACH rec IN recommendations DO
        IF NOT briefsByOwner.has(rec.ownerId) THEN
            briefsByOwner.set(rec.ownerId, new OwnerBrief(rec.ownerId))
        END IF

        brief ← briefsByOwner.get(rec.ownerId)
        brief.addRecommendation(rec)
    END FOR

    // Enhance each brief with summaries
    FOR EACH (ownerId, brief) IN briefsByOwner DO
        brief.summary ← GenerateBriefSummary(brief.recommendations)
        brief.priorityAccounts ← ExtractPriorityAccounts(brief.recommendations)
        brief.actionableCount ← CountActionable(brief.recommendations)
    END FOR

    RETURN briefsByOwner
END
```

---

## Zoho Data Scout Workflow

### Algorithm: ZohoDataScout Agent

```
ALGORITHM: FetchAccountDetails
INPUT: accountId (string)
OUTPUT: EnrichedAccountData

CONSTANTS:
    CACHE_TTL = 6 hours
    RETRY_ATTEMPTS = 3
    FIELDS_TO_FETCH = [
        "Account_Name", "Account_Owner", "Account_Status",
        "Last_Activity_Date", "Modified_Time", "Total_Revenue",
        "Open_Deals_Count", "Last_Contact", "Industry", "Custom_Fields"
    ]

BEGIN
    // Check cache first
    cacheKey ← "account:" + accountId
    cached ← Cache.get(cacheKey)

    IF cached is not null AND NOT cached.isExpired() THEN
        LOG("Cache hit for account", accountId)
        RETURN cached.data
    END IF

    // Fetch from Zoho CRM
    accountData ← null
    attempt ← 0

    WHILE attempt < RETRY_ATTEMPTS DO
        TRY
            // Use MCP tool to fetch account
            response ← MCP_ZOHO.getAccount(
                accountId: accountId,
                fields: FIELDS_TO_FETCH
            )

            IF response.success THEN
                accountData ← response.data
                BREAK
            ELSE
                LOG("Zoho fetch failed", response.error)
                attempt ← attempt + 1
                Sleep(ExponentialBackoff(attempt))
            END IF

        CATCH error AS e
            LOG_ERROR("Zoho API error", e)
            attempt ← attempt + 1
            Sleep(ExponentialBackoff(attempt))
        END TRY
    END WHILE

    IF accountData is null THEN
        THROW DataScoutException("Failed to fetch account after retries", accountId)
    END IF

    // Enrich with related data
    enrichedData ← EnrichAccountData(accountData, accountId)

    // Update cache
    Cache.set(cacheKey, enrichedData, CACHE_TTL)

    RETURN enrichedData
END

SUBROUTINE: EnrichAccountData
INPUT: baseData, accountId
OUTPUT: EnrichedAccountData

BEGIN
    enriched ← new EnrichedAccountData(baseData)

    // Fetch related entities in parallel
    PARALLEL_EXECUTE [
        enriched.deals ← FetchRelatedDeals(accountId),
        enriched.contacts ← FetchRelatedContacts(accountId),
        enriched.activities ← FetchRecentActivities(accountId, 30 days),
        enriched.notes ← FetchRecentNotes(accountId, 90 days)
    ]

    // Detect changes since last review
    enriched.changeFlags ← DetectAccountChanges(enriched, accountId)

    RETURN enriched
END

SUBROUTINE: DetectAccountChanges
INPUT: enrichedData, accountId
OUTPUT: Set<ChangeType>

BEGIN
    changes ← new Set()

    // Retrieve last known state from memory
    lastState ← Memory.retrieve("account_state:" + accountId)

    IF lastState is null THEN
        // First time seeing this account
        changes.add(NEW_ACCOUNT)
        RETURN changes
    END IF

    // Compare owner
    IF enrichedData.ownerId != lastState.ownerId THEN
        changes.add(OWNER_CHANGE)
    END IF

    // Compare status
    IF enrichedData.status != lastState.status THEN
        changes.add(STATUS_CHANGE)
    END IF

    // Check for stalled deals
    FOR EACH deal IN enrichedData.deals DO
        IF deal.stage == lastState.getDealStage(deal.id) THEN
            daysSinceChange ← (CurrentTime() - deal.stageChangedDate).days
            IF daysSinceChange > 30 THEN
                changes.add(DEAL_STALLED)
            END IF
        END IF
    END FOR

    // Check inactivity
    daysSinceActivity ← (CurrentTime() - enrichedData.lastActivityDate).days
    IF daysSinceActivity > 14 THEN
        changes.add(INACTIVITY_THRESHOLD)
    END IF

    // Check for high-value activities
    FOR EACH activity IN enrichedData.activities DO
        IF activity.createdAt > lastState.lastReviewTime THEN
            IF activity.type IN ["Demo", "Contract Review", "Executive Meeting"] THEN
                changes.add(HIGH_VALUE_ACTIVITY)
            END IF
        END IF
    END FOR

    // Store current state for next comparison
    Memory.store("account_state:" + accountId, enrichedData, NO_EXPIRY)

    RETURN changes
END

SUBROUTINE: FetchRelatedDeals
INPUT: accountId
OUTPUT: List<Deal>

BEGIN
    deals ← []

    TRY
        response ← MCP_ZOHO.searchDeals(
            criteria: {
                "Account_Id": accountId,
                "Status": ["Open", "In Progress"]
            },
            fields: ["Deal_Name", "Amount", "Stage", "Probability", "Closing_Date"]
        )

        IF response.success THEN
            deals ← response.data
        END IF

    CATCH error AS e
        LOG_ERROR("Failed to fetch deals", accountId, e)
        // Non-critical: continue without deal data
    END TRY

    RETURN deals
END

SUBROUTINE: FetchRecentActivities
INPUT: accountId, timeWindow
OUTPUT: List<Activity>

BEGIN
    activities ← []
    cutoffDate ← CurrentTime() - timeWindow

    TRY
        response ← MCP_ZOHO.getActivities(
            accountId: accountId,
            modifiedSince: cutoffDate,
            types: ["Call", "Email", "Meeting", "Task"],
            limit: 100
        )

        IF response.success THEN
            activities ← response.data
        END IF

    CATCH error AS e
        LOG_ERROR("Failed to fetch activities", accountId, e)
    END TRY

    RETURN activities
END

ALGORITHM: FetchAccounts
INPUT: filterCriteria
OUTPUT: List<AccountRecord>

BEGIN
    accounts ← []
    pageToken ← null

    REPEAT
        TRY
            response ← MCP_ZOHO.listAccounts(
                filter: filterCriteria,
                pageSize: 200,
                pageToken: pageToken
            )

            IF response.success THEN
                accounts.extend(response.data)
                pageToken ← response.nextPageToken
            ELSE
                LOG_ERROR("Failed to fetch accounts page", response.error)
                BREAK
            END IF

        CATCH error AS e
            LOG_ERROR("Zoho list accounts error", e)
            BREAK
        END TRY

    UNTIL pageToken is null OR accounts.size >= filterCriteria.maxResults

    RETURN accounts
END
```

### Decision Tree: Change Detection Routing

```
DECISION TREE: Route Account by Change Type

Account has changes?
├─ NO → Skip (no action needed)
└─ YES → Classify urgency
    ├─ CRITICAL (Owner change, Deal stalled >45 days, Status→AtRisk)
    │   └─ Priority: 1 (immediate processing)
    ├─ HIGH (High-value activity, New contact, Deal stalled >30 days)
    │   └─ Priority: 2 (process within 1 hour)
    ├─ MEDIUM (Inactivity >14 days, Custom field modified)
    │   └─ Priority: 3 (process within 6 hours)
    └─ LOW (Minor updates)
        └─ Priority: 4 (process within 24 hours)
```

---

## Memory Analyst Workflow

### Algorithm: MemoryAnalyst Agent

```
ALGORITHM: AnalyzeAccountHistory
INPUT: accountId (string)
OUTPUT: HistoricalContext

CONSTANTS:
    LOOKBACK_PERIOD = 365 days
    MAX_EVENTS = 200
    INSIGHT_CONFIDENCE_THRESHOLD = 0.6

BEGIN
    context ← new HistoricalContext(accountId)

    // Phase 1: Retrieve stored timeline
    timeline ← RetrieveTimeline(accountId, LOOKBACK_PERIOD)
    context.timeline ← timeline

    // Phase 2: Query Cognee for semantic insights
    insights ← QueryCogneeForInsights(accountId, timeline)
    context.keyInsights ← FilterInsightsByConfidence(insights, INSIGHT_CONFIDENCE_THRESHOLD)

    // Phase 3: Retrieve prior recommendations
    priorRecs ← RetrievePriorRecommendations(accountId, 180 days)
    context.priorRecommendations ← priorRecs

    // Phase 4: Calculate engagement metrics
    context.sentimentTrend ← AnalyzeSentimentTrend(timeline)
    context.engagementScore ← CalculateEngagementScore(timeline)

    // Phase 5: Store enriched context for future reference
    StoreEnrichedContext(accountId, context)

    RETURN context
END

SUBROUTINE: RetrieveTimeline
INPUT: accountId, lookbackPeriod
OUTPUT: List<TimelineEvent>

BEGIN
    timeline ← []
    cutoffDate ← CurrentTime() - lookbackPeriod

    // Retrieve from Cognee memory
    TRY
        query ← BuildCogneeQuery(
            accountId: accountId,
            startDate: cutoffDate,
            eventTypes: ["meeting", "call", "email", "deal_update", "note"],
            orderBy: "timestamp DESC",
            limit: MAX_EVENTS
        )

        response ← MCP_COGNEE.search(query)

        IF response.success THEN
            FOR EACH item IN response.data DO
                event ← ParseTimelineEvent(item)
                timeline.append(event)
            END FOR
        END IF

    CATCH error AS e
        LOG_ERROR("Failed to retrieve timeline from Cognee", accountId, e)
        // Fallback: construct timeline from Zoho data
        timeline ← FallbackTimelineFromZoho(accountId, cutoffDate)
    END TRY

    // Sort by timestamp descending
    timeline.sort(key: timestamp, order: DESC)

    RETURN timeline
END

SUBROUTINE: QueryCogneeForInsights
INPUT: accountId, timeline
OUTPUT: List<Insight>

BEGIN
    insights ← []

    // Construct semantic query for Cognee
    queryContext ← BuildSemanticContext(accountId, timeline)

    TRY
        // Query for risk indicators
        riskQuery ← "risks, challenges, blockers related to account " + accountId
        riskInsights ← MCP_COGNEE.queryInsights(riskQuery, queryContext)
        insights.extend(MapToInsightStructure(riskInsights, "Risk"))

        // Query for opportunities
        oppQuery ← "opportunities, growth, expansion related to account " + accountId
        oppInsights ← MCP_COGNEE.queryInsights(oppQuery, queryContext)
        insights.extend(MapToInsightStructure(oppInsights, "Opportunity"))

        // Query for patterns
        patternQuery ← "recurring patterns, trends, behaviors for account " + accountId
        patternInsights ← MCP_COGNEE.queryInsights(patternQuery, queryContext)
        insights.extend(MapToInsightStructure(patternInsights, "Pattern"))

        // Query for commitments
        commitQuery ← "promises, commitments, follow-ups related to account " + accountId
        commitInsights ← MCP_COGNEE.queryInsights(commitQuery, queryContext)
        insights.extend(MapToInsightStructure(commitInsights, "Commitment"))

    CATCH error AS e
        LOG_ERROR("Cognee query failed", accountId, e)
        // Continue with empty insights
    END TRY

    RETURN insights
END

SUBROUTINE: BuildSemanticContext
INPUT: accountId, timeline
OUTPUT: string (contextual prompt)

BEGIN
    // Extract key facts from timeline
    recentEvents ← timeline.slice(0, 10)
    keyContacts ← ExtractUniqueContacts(recentEvents)
    recentTopics ← ExtractTopics(recentEvents)

    context ← "Account ID: " + accountId + "\n"
    context ← context + "Recent activity summary:\n"

    FOR EACH event IN recentEvents DO
        context ← context + "- " + event.description + " (" + event.timestamp + ")\n"
    END FOR

    context ← context + "\nKey contacts: " + Join(keyContacts, ", ") + "\n"
    context ← context + "Discussion topics: " + Join(recentTopics, ", ") + "\n"

    RETURN context
END

SUBROUTINE: FilterInsightsByConfidence
INPUT: insights, threshold
OUTPUT: List<Insight>

BEGIN
    filtered ← []

    FOR EACH insight IN insights DO
        IF insight.confidence >= threshold THEN
            filtered.append(insight)
        END IF
    END FOR

    // Sort by confidence descending
    filtered.sort(key: confidence, order: DESC)

    RETURN filtered
END

SUBROUTINE: AnalyzeSentimentTrend
INPUT: timeline
OUTPUT: SentimentTrend enum

BEGIN
    IF timeline is empty OR timeline.size < 3 THEN
        RETURN Unknown
    END IF

    // Analyze sentiment of recent events
    sentimentScores ← []

    FOR EACH event IN timeline.slice(0, 10) DO
        score ← ExtractSentimentFromDescription(event.description)
        IF score is not null THEN
            sentimentScores.append(score)
        END IF
    END FOR

    IF sentimentScores is empty THEN
        RETURN Unknown
    END IF

    // Calculate trend
    recentAvg ← Average(sentimentScores.slice(0, 3))
    olderAvg ← Average(sentimentScores.slice(3, 10))

    delta ← recentAvg - olderAvg

    IF delta > 0.2 THEN
        RETURN Improving
    ELSE IF delta < -0.2 THEN
        RETURN Declining
    ELSE
        RETURN Stable
    END IF
END

SUBROUTINE: CalculateEngagementScore
INPUT: timeline
OUTPUT: float (0.0-1.0)

BEGIN
    IF timeline is empty THEN
        RETURN 0.0
    END IF

    score ← 0.0

    // Recent activity score (40% weight)
    daysSinceLastActivity ← (CurrentTime() - timeline[0].timestamp).days
    activityScore ← MAX(0, 1.0 - (daysSinceLastActivity / 30.0))
    score ← score + (activityScore * 0.4)

    // Activity frequency score (30% weight)
    last30Days ← CountEventsInWindow(timeline, 30 days)
    frequencyScore ← MIN(1.0, last30Days / 10.0)
    score ← score + (frequencyScore * 0.3)

    // Quality of engagement (30% weight)
    highValueEvents ← CountHighValueEvents(timeline, 90 days)
    qualityScore ← MIN(1.0, highValueEvents / 5.0)
    score ← score + (qualityScore * 0.3)

    RETURN MIN(1.0, score)
END

SUBROUTINE: RetrievePriorRecommendations
INPUT: accountId, lookbackPeriod
OUTPUT: List<PastRecommendation>

BEGIN
    priorRecs ← []
    cutoffDate ← CurrentTime() - lookbackPeriod

    TRY
        // Query recommendation history from memory
        query ← {
            "accountId": accountId,
            "generatedAfter": cutoffDate,
            "includeStatus": true
        }

        response ← Memory.query("recommendations", query)

        IF response.success THEN
            FOR EACH rec IN response.data DO
                priorRecs.append(rec)
            END FOR
        END IF

    CATCH error AS e
        LOG_ERROR("Failed to retrieve prior recommendations", accountId, e)
    END TRY

    RETURN priorRecs
END

SUBROUTINE: StoreEnrichedContext
INPUT: accountId, context
OUTPUT: void

BEGIN
    TRY
        // Store in Cognee for future semantic queries
        MCP_COGNEE.ingest(
            entityType: "account_context",
            entityId: accountId,
            data: context,
            timestamp: CurrentTime()
        )

        // Also store in local memory for quick retrieval
        Memory.store(
            "context:" + accountId,
            context,
            TTL: 24 hours
        )

    CATCH error AS e
        LOG_ERROR("Failed to store enriched context", accountId, e)
    END TRY
END
```

---

## Recommendation Author Workflow

### Algorithm: RecommendationAuthor Agent

```
ALGORITHM: GenerateRecommendations
INPUT:
    accountData (EnrichedAccountData)
    historicalContext (HistoricalContext)
    runConfig (configuration)
OUTPUT:
    List<Recommendation>

CONSTANTS:
    MIN_CONFIDENCE = 0.5
    MAX_RECOMMENDATIONS_PER_ACCOUNT = 5

BEGIN
    recommendations ← []

    // Analyze current state and context
    analysisResult ← AnalyzeAccountSituation(accountData, historicalContext)

    // Generate candidate recommendations
    candidates ← []

    // Rule-based recommendation generation
    candidates.extend(GenerateRuleBased(accountData, analysisResult))

    // Pattern-based recommendations from historical data
    candidates.extend(GeneratePatternBased(historicalContext, analysisResult))

    // Change-driven recommendations
    FOR EACH changeFlag IN accountData.changeFlags DO
        candidates.extend(GenerateChangeBasedRecs(changeFlag, accountData, historicalContext))
    END FOR

    // Score and filter candidates
    FOR EACH candidate IN candidates DO
        candidate.confidence ← CalculateConfidence(candidate, accountData, historicalContext)
    END FOR

    // Filter by confidence threshold
    filtered ← []
    FOR EACH candidate IN candidates WHERE candidate.confidence >= MIN_CONFIDENCE DO
        filtered.append(candidate)
    END FOR

    // Rank by priority and confidence
    ranked ← RankRecommendations(filtered, runConfig.priorityWeights)

    // Take top N recommendations
    recommendations ← ranked.slice(0, MAX_RECOMMENDATIONS_PER_ACCOUNT)

    // Enrich with supporting data and rationale
    FOR EACH rec IN recommendations DO
        EnrichRecommendation(rec, accountData, historicalContext)
    END FOR

    RETURN recommendations
END

SUBROUTINE: AnalyzeAccountSituation
INPUT: accountData, historicalContext
OUTPUT: SituationAnalysis

BEGIN
    analysis ← new SituationAnalysis()

    // Risk assessment
    analysis.riskLevel ← AssessRiskLevel(accountData, historicalContext)
    analysis.riskFactors ← IdentifyRiskFactors(accountData, historicalContext)

    // Opportunity assessment
    analysis.opportunities ← IdentifyOpportunities(accountData, historicalContext)

    // Engagement health
    analysis.engagementHealth ← historicalContext.engagementScore
    analysis.sentimentTrend ← historicalContext.sentimentTrend

    // Commitment tracking
    analysis.openCommitments ← ExtractOpenCommitments(historicalContext)
    analysis.overdueCommitments ← FilterOverdueCommitments(analysis.openCommitments)

    RETURN analysis
END

SUBROUTINE: AssessRiskLevel
INPUT: accountData, historicalContext
OUTPUT: enum {Critical, High, Medium, Low}

BEGIN
    riskScore ← 0

    // Inactivity risk
    daysSinceActivity ← (CurrentTime() - accountData.lastActivityDate).days
    IF daysSinceActivity > 30 THEN
        riskScore ← riskScore + 40
    ELSE IF daysSinceActivity > 14 THEN
        riskScore ← riskScore + 20
    END IF

    // Sentiment risk
    IF historicalContext.sentimentTrend == Declining THEN
        riskScore ← riskScore + 30
    END IF

    // Engagement risk
    IF historicalContext.engagementScore < 0.3 THEN
        riskScore ← riskScore + 25
    END IF

    // Stalled deals
    stalledDeals ← CountStalledDeals(accountData.deals)
    riskScore ← riskScore + (stalledDeals * 15)

    // Overdue commitments
    overdueCount ← CountOverdueCommitments(historicalContext)
    riskScore ← riskScore + (overdueCount * 20)

    // Categorize
    IF riskScore >= 80 THEN
        RETURN Critical
    ELSE IF riskScore >= 50 THEN
        RETURN High
    ELSE IF riskScore >= 25 THEN
        RETURN Medium
    ELSE
        RETURN Low
    END IF
END

SUBROUTINE: GenerateRuleBased
INPUT: accountData, analysisResult
OUTPUT: List<RecommendationCandidate>

BEGIN
    candidates ← []

    // Rule 1: High-risk accounts need immediate outreach
    IF analysisResult.riskLevel IN [Critical, High] THEN
        candidate ← new RecommendationCandidate(
            actionType: FollowUp,
            title: "Immediate check-in required for at-risk account",
            suggestedActions: [
                CreateAction("Schedule call within 48 hours"),
                CreateAction("Review account health with team")
            ]
        )
        candidates.append(candidate)
    END IF

    // Rule 2: Stalled deals need intervention
    stalledDeals ← FilterStalledDeals(accountData.deals, 30 days)
    IF NOT stalledDeals.isEmpty() THEN
        FOR EACH deal IN stalledDeals DO
            candidate ← new RecommendationCandidate(
                actionType: Escalate,
                title: "Deal stalled for " + deal.daysSinceChange + " days",
                suggestedActions: [
                    CreateAction("Schedule stakeholder meeting to unblock"),
                    CreateAction("Review deal requirements and timeline")
                ]
            )
            candidates.append(candidate)
        END FOR
    END IF

    // Rule 3: Overdue commitments need resolution
    IF NOT analysisResult.overdueCommitments.isEmpty() THEN
        candidate ← new RecommendationCandidate(
            actionType: FollowUp,
            title: "Address " + analysisResult.overdueCommitments.size + " overdue commitments",
            suggestedActions: [
                CreateAction("Follow up on pending deliverables"),
                CreateAction("Reset expectations if needed")
            ]
        )
        candidates.append(candidate)
    END IF

    // Rule 4: Low engagement accounts need re-engagement
    IF analysisResult.engagementHealth < 0.4 THEN
        candidate ← new RecommendationCandidate(
            actionType: Monitor,
            title: "Re-engagement campaign for low-activity account",
            suggestedActions: [
                CreateAction("Share relevant case study or industry insight"),
                CreateAction("Invite to upcoming event or webinar")
            ]
        )
        candidates.append(candidate)
    END IF

    // Rule 5: Positive sentiment with opportunities
    IF analysisResult.sentimentTrend == Improving AND NOT analysisResult.opportunities.isEmpty() THEN
        candidate ← new RecommendationCandidate(
            actionType: Schedule,
            title: "Capitalize on positive momentum",
            suggestedActions: [
                CreateAction("Discuss expansion opportunities"),
                CreateAction("Request referral or case study")
            ]
        )
        candidates.append(candidate)
    END IF

    RETURN candidates
END

SUBROUTINE: GeneratePatternBased
INPUT: historicalContext, analysisResult
OUTPUT: List<RecommendationCandidate>

BEGIN
    candidates ← []

    // Analyze successful patterns from history
    FOR EACH insight IN historicalContext.keyInsights DO
        IF insight.category == Pattern AND insight.confidence > 0.7 THEN
            // Identify actionable pattern
            IF insight.description.contains("successful when") THEN
                candidate ← CreatePatternBasedRecommendation(insight)
                candidates.append(candidate)
            END IF
        END IF
    END FOR

    // Learn from prior recommendations
    FOR EACH priorRec IN historicalContext.priorRecommendations DO
        IF priorRec.status == Approved AND priorRec.outcome == Successful THEN
            // Check if similar situation exists now
            IF IsSimilarSituation(priorRec.context, analysisResult) THEN
                candidate ← AdaptPriorRecommendation(priorRec, analysisResult)
                candidates.append(candidate)
            END IF
        END IF
    END FOR

    RETURN candidates
END

SUBROUTINE: GenerateChangeBasedRecs
INPUT: changeFlag, accountData, historicalContext
OUTPUT: List<RecommendationCandidate>

BEGIN
    candidates ← []

    SWITCH changeFlag DO
        CASE OWNER_CHANGE:
            candidate ← new RecommendationCandidate(
                actionType: FollowUp,
                title: "Transition support for new account owner",
                suggestedActions: [
                    CreateAction("Schedule handoff call with previous owner"),
                    CreateAction("Review account history and key relationships"),
                    CreateAction("Introduce new owner to key contacts")
                ]
            )
            candidates.append(candidate)

        CASE DEAL_STALLED:
            candidate ← new RecommendationCandidate(
                actionType: Escalate,
                title: "Intervene on stalled deal progression",
                suggestedActions: [
                    CreateAction("Identify blockers in current stage"),
                    CreateAction("Engage executive sponsor if needed"),
                    CreateAction("Propose alternative path forward")
                ]
            )
            candidates.append(candidate)

        CASE INACTIVITY_THRESHOLD:
            candidate ← new RecommendationCandidate(
                actionType: Monitor,
                title: "Re-establish contact after inactivity period",
                suggestedActions: [
                    CreateAction("Send value-add content or insight"),
                    CreateAction("Request brief check-in call"),
                    CreateAction("Assess continued fit and interest")
                ]
            )
            candidates.append(candidate)

        CASE HIGH_VALUE_ACTIVITY:
            candidate ← new RecommendationCandidate(
                actionType: FollowUp,
                title: "Capitalize on recent high-value interaction",
                suggestedActions: [
                    CreateAction("Send follow-up with key takeaways"),
                    CreateAction("Propose next steps or deliverables"),
                    CreateAction("Request feedback on discussion")
                ]
            )
            candidates.append(candidate)

        DEFAULT:
            // No specific recommendation for this change type
    END SWITCH

    RETURN candidates
END

SUBROUTINE: CalculateConfidence
INPUT: candidate, accountData, historicalContext
OUTPUT: float (0.0-1.0)

BEGIN
    confidence ← 0.5  // Base confidence

    // Factor 1: Data completeness (30% weight)
    dataCompleteness ← AssessDataCompleteness(accountData)
    confidence ← confidence + (dataCompleteness * 0.3)

    // Factor 2: Historical success rate (25% weight)
    IF candidate.basedOnPattern THEN
        historicalSuccess ← GetPatternSuccessRate(candidate.pattern)
        confidence ← confidence + (historicalSuccess * 0.25)
    END IF

    // Factor 3: Insight confidence (20% weight)
    IF candidate.basedOnInsight THEN
        insightConf ← candidate.sourceInsight.confidence
        confidence ← confidence + (insightConf * 0.2)
    ELSE
        confidence ← confidence + 0.1  // Lower boost for rule-based
    END IF

    // Factor 4: Recency of data (15% weight)
    recencyScore ← CalculateRecencyScore(accountData.lastModified)
    confidence ← confidence + (recencyScore * 0.15)

    // Factor 5: Alignment with prior successful actions (10% weight)
    alignmentScore ← AssessAlignmentWithHistory(candidate, historicalContext)
    confidence ← confidence + (alignmentScore * 0.1)

    // Normalize to [0, 1]
    RETURN MIN(1.0, MAX(0.0, confidence))
END

SUBROUTINE: RankRecommendations
INPUT: recommendations, priorityWeights
OUTPUT: List<Recommendation> (sorted)

BEGIN
    // Calculate composite score for each recommendation
    FOR EACH rec IN recommendations DO
        score ← 0.0

        // Priority weight
        SWITCH rec.priority DO
            CASE Critical:
                score ← score + (priorityWeights.critical * 100)
            CASE High:
                score ← score + (priorityWeights.high * 75)
            CASE Medium:
                score ← score + (priorityWeights.medium * 50)
            CASE Low:
                score ← score + (priorityWeights.low * 25)
        END SWITCH

        // Confidence weight
        score ← score + (rec.confidence * 50)

        // Action complexity (prefer simpler actions)
        complexity ← SumActionComplexity(rec.suggestedActions)
        score ← score - (complexity * 5)

        rec.rankScore ← score
    END FOR

    // Sort by rank score descending
    recommendations.sort(key: rankScore, order: DESC)

    RETURN recommendations
END

SUBROUTINE: EnrichRecommendation
INPUT: rec, accountData, historicalContext
OUTPUT: void (modifies rec in place)

BEGIN
    // Build rationale
    rationale ← "Based on:\n"

    // Add change flags to rationale
    IF NOT accountData.changeFlags.isEmpty() THEN
        rationale ← rationale + "- Recent changes: " + Join(accountData.changeFlags, ", ") + "\n"
    END IF

    // Add risk factors
    IF rec.priority IN [Critical, High] THEN
        riskFactors ← IdentifyRiskFactors(accountData, historicalContext)
        rationale ← rationale + "- Risk indicators: " + Join(riskFactors, ", ") + "\n"
    END IF

    // Add supporting insights
    relevantInsights ← FilterRelevantInsights(historicalContext.keyInsights, rec)
    FOR EACH insight IN relevantInsights.slice(0, 3) DO
        rationale ← rationale + "- " + insight.description + "\n"
    END FOR

    rec.rationale ← rationale

    // Add supporting data references
    rec.supportingData ← []
    rec.supportingData.append(CreateDataRef("Account", accountData.accountId))

    FOR EACH insight IN relevantInsights DO
        FOR EACH ref IN insight.evidenceReferences DO
            rec.supportingData.append(CreateDataRef("Evidence", ref))
        END FOR
    END FOR

    // Generate draft content for actions
    FOR EACH action IN rec.suggestedActions DO
        IF action.actionType == "Send email" THEN
            action.draftContent ← GenerateEmailDraft(accountData, rec)
        ELSE IF action.actionType == "Create task" THEN
            action.crmUpdates ← GenerateTaskCRMUpdates(accountData, action)
        END IF
    END FOR

    // Set expiration
    rec.expiresAt ← CurrentTime() + CalculateExpirationWindow(rec.priority)
END

SUBROUTINE: GenerateEmailDraft
INPUT: accountData, recommendation
OUTPUT: string (email draft)

BEGIN
    draft ← "Subject: " + recommendation.title + "\n\n"
    draft ← draft + "Hi [Contact Name],\n\n"

    // Opening based on context
    IF accountData.changeFlags.contains(INACTIVITY_THRESHOLD) THEN
        draft ← draft + "I wanted to reach out as it's been a while since we last connected. "
    ELSE IF accountData.changeFlags.contains(HIGH_VALUE_ACTIVITY) THEN
        draft ← draft + "Following up on our recent conversation, "
    ELSE
        draft ← draft + "I hope this message finds you well. "
    END IF

    // Body based on recommendation
    draft ← draft + recommendation.rationale + "\n\n"

    // Call to action
    draft ← draft + "I'd like to suggest we:\n"
    FOR EACH action IN recommendation.suggestedActions DO
        draft ← draft + "- " + action.description + "\n"
    END FOR

    draft ← draft + "\nWould you have time for a brief call this week?\n\n"
    draft ← draft + "Best regards,\n[Your Name]"

    RETURN draft
END
```

---

## Approval Gate Mechanism

### Algorithm: ApprovalGate

```
ALGORITHM: RequestApproval
INPUT:
    recommendations (List<Recommendation>)
    targetOwner (string)
    channel (enum {CLI, Email, Slack, UI})
OUTPUT:
    approvalResults (Map<recommendationId, ApprovalDecision>)

BEGIN
    approvalResults ← new Map()

    // Group recommendations by account for better UX
    byAccount ← GroupByAccount(recommendations)

    // Format approval request
    requestPayload ← FormatApprovalRequest(byAccount, targetOwner)

    // Send via configured channel
    requestId ← SendApprovalRequest(requestPayload, channel)

    // Wait for response with timeout
    response ← WaitForApprovalResponse(requestId, TIMEOUT: 72 hours)

    IF response is null THEN
        // Timeout: mark all as expired
        FOR EACH rec IN recommendations DO
            approvalResults.set(rec.recommendationId, ApprovalDecision(
                status: Expired,
                reason: "No response within approval window"
            ))
        END FOR
    ELSE
        // Process decisions
        FOR EACH decision IN response.decisions DO
            approvalResults.set(decision.recommendationId, decision)
        END FOR
    END IF

    // Log approval outcomes
    FOR EACH (recId, decision) IN approvalResults DO
        LogApprovalDecision(recId, targetOwner, decision)
    END FOR

    RETURN approvalResults
END

SUBROUTINE: FormatApprovalRequest
INPUT: recommendationsByAccount, targetOwner
OUTPUT: ApprovalRequestPayload

BEGIN
    payload ← new ApprovalRequestPayload()
    payload.ownerId ← targetOwner
    payload.requestId ← GenerateUUID()
    payload.createdAt ← CurrentTime()
    payload.expiresAt ← CurrentTime() + 72 hours

    // Summary section
    payload.summary ← new Summary()
    payload.summary.totalRecommendations ← CountAllRecommendations(recommendationsByAccount)
    payload.summary.criticalCount ← CountByPriority(recommendationsByAccount, Critical)
    payload.summary.highCount ← CountByPriority(recommendationsByAccount, High)

    // Account-specific sections
    payload.accounts ← []
    FOR EACH (accountId, recs) IN recommendationsByAccount DO
        accountSection ← new AccountSection()
        accountSection.accountId ← accountId
        accountSection.accountName ← recs[0].accountName
        accountSection.recommendations ← FormatRecommendationsForDisplay(recs)
        payload.accounts.append(accountSection)
    END FOR

    RETURN payload
END

SUBROUTINE: FormatRecommendationsForDisplay
INPUT: recommendations
OUTPUT: List<DisplayRecommendation>

BEGIN
    display ← []

    FOR EACH rec IN recommendations DO
        item ← new DisplayRecommendation()
        item.id ← rec.recommendationId
        item.priority ← rec.priority
        item.title ← rec.title
        item.rationale ← rec.rationale
        item.confidence ← rec.confidence

        // Format actions
        item.actions ← []
        FOR EACH action IN rec.suggestedActions DO
            item.actions.append({
                description: action.description,
                estimatedEffort: action.estimatedEffort + " minutes",
                draft: action.draftContent (if available)
            })
        END FOR

        // Default options
        item.options ← ["Approve", "Modify", "Reject", "Defer"]

        display.append(item)
    END FOR

    RETURN display
END

SUBROUTINE: SendApprovalRequest
INPUT: payload, channel
OUTPUT: string (requestId)

BEGIN
    requestId ← payload.requestId

    SWITCH channel DO
        CASE CLI:
            SaveApprovalRequestToFile(payload, "./approvals/" + requestId + ".json")
            PrintCLINotification(payload)

        CASE Email:
            emailBody ← RenderEmailTemplate(payload)
            SendEmail(
                to: GetOwnerEmail(payload.ownerId),
                subject: "Account Recommendations Pending Your Review",
                body: emailBody,
                replyTracking: requestId
            )

        CASE Slack:
            slackMessage ← RenderSlackBlocks(payload)
            PostToSlack(
                channel: GetOwnerSlackChannel(payload.ownerId),
                blocks: slackMessage,
                callbackId: requestId
            )

        CASE UI:
            StoreInApprovalQueue(payload)
            NotifyUI(payload.ownerId, requestId)

        DEFAULT:
            THROW ApprovalException("Unsupported approval channel: " + channel)
    END SWITCH

    // Track request for monitoring
    TrackApprovalRequest(requestId, payload.ownerId, CurrentTime())

    RETURN requestId
END

SUBROUTINE: WaitForApprovalResponse
INPUT: requestId, timeout
OUTPUT: ApprovalResponse or null

BEGIN
    deadline ← CurrentTime() + timeout
    checkInterval ← 5 minutes

    WHILE CurrentTime() < deadline DO
        // Check for response
        response ← CheckApprovalStatus(requestId)

        IF response is not null AND response.completed THEN
            RETURN response
        END IF

        // Wait before next check
        Sleep(checkInterval)
    END WHILE

    // Timeout reached
    RETURN null
END

SUBROUTINE: CheckApprovalStatus
INPUT: requestId
OUTPUT: ApprovalResponse or null

BEGIN
    // Check different sources based on original channel

    // Check file system (CLI)
    responsePath ← "./approvals/" + requestId + "_response.json"
    IF FileExists(responsePath) THEN
        RETURN LoadApprovalResponse(responsePath)
    END IF

    // Check email replies (Email channel)
    emailResponse ← CheckEmailReplies(requestId)
    IF emailResponse is not null THEN
        RETURN ParseEmailResponse(emailResponse)
    END IF

    // Check Slack interactions (Slack channel)
    slackResponse ← CheckSlackInteractions(requestId)
    IF slackResponse is not null THEN
        RETURN ParseSlackResponse(slackResponse)
    END IF

    // Check UI database (UI channel)
    uiResponse ← QueryApprovalDatabase(requestId)
    IF uiResponse is not null AND uiResponse.completed THEN
        RETURN uiResponse
    END IF

    // No response yet
    RETURN null
END

ALGORITHM: ExecuteApprovedActions
INPUT: recommendation, approvalDecision
OUTPUT: ExecutionResult

BEGIN
    result ← new ExecutionResult(recommendation.recommendationId)

    // Validate approval
    IF approvalDecision.status != Approved THEN
        result.status ← Skipped
        result.message ← "Recommendation not approved"
        RETURN result
    END IF

    executedActions ← []
    failedActions ← []

    // Execute each approved action
    FOR EACH action IN recommendation.suggestedActions DO
        TRY
            actionResult ← ExecuteSingleAction(action, recommendation)
            executedActions.append(actionResult)

        CATCH error AS e
            LOG_ERROR("Action execution failed", action.actionId, e)
            failedActions.append({
                action: action,
                error: e
            })
        END TRY
    END FOR

    // Determine overall result
    IF failedActions.isEmpty() THEN
        result.status ← Success
        result.message ← "All actions executed successfully"
    ELSE IF executedActions.isEmpty() THEN
        result.status ← Failed
        result.message ← "All actions failed"
    ELSE
        result.status ← PartialSuccess
        result.message ← "Some actions failed"
    END IF

    result.executedActions ← executedActions
    result.failedActions ← failedActions

    // Log execution outcome
    LogExecutionResult(result)

    // Update recommendation status
    UpdateRecommendationStatus(recommendation.recommendationId, result.status)

    RETURN result
END

SUBROUTINE: ExecuteSingleAction
INPUT: action, recommendation
OUTPUT: ActionExecutionResult

BEGIN
    result ← new ActionExecutionResult(action.actionId)

    SWITCH action.actionType DO
        CASE "Send email":
            emailId ← SendEmailViaZoho(
                accountId: recommendation.accountId,
                subject: ExtractSubject(action.draftContent),
                body: action.draftContent
            )
            result.crmReference ← emailId
            result.status ← Success

        CASE "Create task":
            taskId ← CreateZohoTask(
                accountId: recommendation.accountId,
                title: action.description,
                dueDate: CalculateDueDate(recommendation.priority),
                ownerId: recommendation.ownerId,
                additionalFields: action.crmUpdates
            )
            result.crmReference ← taskId
            result.status ← Success

        CASE "Update account":
            // Requires approval for write operations
            IF action.crmUpdates is not null THEN
                updated ← UpdateZohoAccount(
                    accountId: recommendation.accountId,
                    updates: action.crmUpdates
                )
                result.crmReference ← recommendation.accountId
                result.status ← Success
            END IF

        CASE "Schedule meeting":
            meetingId ← CreateMeetingInvite(
                accountId: recommendation.accountId,
                title: action.description,
                proposedTimes: action.metadata.timeSlots
            )
            result.crmReference ← meetingId
            result.status ← Success

        DEFAULT:
            result.status ← Skipped
            result.message ← "Action type not supported for execution"
    END SWITCH

    RETURN result
END
```

### Decision Tree: Approval Processing

```
DECISION TREE: Process Approval Response

Response received?
├─ NO (timeout) → Mark all as Expired → Notify owner
└─ YES → Parse decisions
    ├─ For each recommendation:
    │   ├─ APPROVED → Execute actions → Log success/failures
    │   ├─ MODIFIED → Parse modifications → Execute modified actions
    │   ├─ REJECTED → Log reason → Update status
    │   └─ DEFERRED → Reschedule for later review
    └─ Generate execution report → Send to owner
```

---

## Error Handling & Retry Logic

### Algorithm: ErrorHandler

```
ALGORITHM: HandleOperationWithRetry
INPUT:
    operation (function)
    maxRetries (integer)
    backoffStrategy (enum)
OUTPUT:
    result or exception

CONSTANTS:
    INITIAL_BACKOFF = 1 second
    MAX_BACKOFF = 60 seconds
    BACKOFF_MULTIPLIER = 2

BEGIN
    attempt ← 0
    lastError ← null

    WHILE attempt < maxRetries DO
        TRY
            result ← operation()
            RETURN result

        CATCH error AS e
            attempt ← attempt + 1
            lastError ← e

            // Classify error
            errorType ← ClassifyError(e)

            SWITCH errorType DO
                CASE Transient:
                    // Retry with backoff
                    IF attempt < maxRetries THEN
                        backoffTime ← CalculateBackoff(attempt, backoffStrategy)
                        LOG("Transient error, retrying in {time}", backoffTime, attempt)
                        Sleep(backoffTime)
                    END IF

                CASE RateLimited:
                    // Honor rate limit with longer backoff
                    retryAfter ← ExtractRetryAfter(e) OR (INITIAL_BACKOFF * BACKOFF_MULTIPLIER ^ attempt)
                    LOG("Rate limited, waiting {time}", retryAfter)
                    Sleep(retryAfter)

                CASE Authentication:
                    // Attempt token refresh
                    IF attempt == 0 THEN
                        RefreshAuthToken()
                        // Retry immediately after refresh
                    ELSE
                        THROW e  // Don't retry auth errors multiple times
                    END IF

                CASE Permanent:
                    // Don't retry permanent errors
                    LOG_ERROR("Permanent error encountered", e)
                    THROW e

                CASE Unknown:
                    // Treat as transient but log for investigation
                    LOG_WARNING("Unknown error type, treating as transient", e)
                    IF attempt < maxRetries THEN
                        Sleep(CalculateBackoff(attempt, backoffStrategy))
                    END IF

                DEFAULT:
                    THROW e
            END SWITCH
        END TRY
    END WHILE

    // Max retries exhausted
    LOG_ERROR("Operation failed after {count} retries", maxRetries, lastError)
    THROW RetryExhaustedException(maxRetries, lastError)
END

SUBROUTINE: CalculateBackoff
INPUT: attempt, strategy
OUTPUT: milliseconds

BEGIN
    SWITCH strategy DO
        CASE Exponential:
            backoff ← INITIAL_BACKOFF * (BACKOFF_MULTIPLIER ^ (attempt - 1))
            RETURN MIN(backoff, MAX_BACKOFF)

        CASE Linear:
            backoff ← INITIAL_BACKOFF * attempt
            RETURN MIN(backoff, MAX_BACKOFF)

        CASE Fixed:
            RETURN INITIAL_BACKOFF

        CASE ExponentialWithJitter:
            baseBackoff ← INITIAL_BACKOFF * (BACKOFF_MULTIPLIER ^ (attempt - 1))
            jitter ← Random(0, baseBackoff * 0.25)
            RETURN MIN(baseBackoff + jitter, MAX_BACKOFF)

        DEFAULT:
            RETURN INITIAL_BACKOFF
    END SWITCH
END

SUBROUTINE: ClassifyError
INPUT: error
OUTPUT: ErrorType enum

BEGIN
    // Check error message/code patterns
    message ← error.message.toLowerCase()
    code ← error.code

    // Network/timeout errors
    IF message.contains("timeout") OR
       message.contains("connection refused") OR
       code IN [ECONNREFUSED, ETIMEDOUT] THEN
        RETURN Transient
    END IF

    // Rate limiting
    IF code IN [429, 503] OR
       message.contains("rate limit") OR
       message.contains("too many requests") THEN
        RETURN RateLimited
    END IF

    // Authentication
    IF code IN [401, 403] OR
       message.contains("unauthorized") OR
       message.contains("authentication") THEN
        RETURN Authentication
    END IF

    // Permanent errors
    IF code IN [400, 404, 422] OR
       message.contains("not found") OR
       message.contains("invalid") THEN
        RETURN Permanent
    END IF

    // Service unavailable (transient)
    IF code == 502 OR code == 504 THEN
        RETURN Transient
    END IF

    // Unknown - treat cautiously
    RETURN Unknown
END

ALGORITHM: CircuitBreaker
STATE: Open, HalfOpen, Closed
PURPOSE: Prevent cascading failures

STRUCTURE: CircuitBreakerState
    status: enum {Closed, Open, HalfOpen}
    failureCount: integer
    lastFailureTime: timestamp
    successCount: integer
    openedAt: timestamp
END STRUCTURE

CONSTANTS:
    FAILURE_THRESHOLD = 5
    TIMEOUT_DURATION = 60 seconds
    HALF_OPEN_SUCCESS_THRESHOLD = 2

BEGIN
    state ← new CircuitBreakerState(status: Closed)

    FUNCTION executeWithCircuitBreaker(operation):
        SWITCH state.status DO
            CASE Closed:
                TRY
                    result ← operation()
                    state.failureCount ← 0
                    RETURN result
                CATCH error
                    state.failureCount ← state.failureCount + 1
                    state.lastFailureTime ← CurrentTime()

                    IF state.failureCount >= FAILURE_THRESHOLD THEN
                        state.status ← Open
                        state.openedAt ← CurrentTime()
                        LOG("Circuit breaker opened after {count} failures", FAILURE_THRESHOLD)
                    END IF

                    THROW error
                END TRY

            CASE Open:
                timeSinceOpened ← CurrentTime() - state.openedAt

                IF timeSinceOpened >= TIMEOUT_DURATION THEN
                    state.status ← HalfOpen
                    state.successCount ← 0
                    LOG("Circuit breaker entering half-open state")
                    RETURN executeWithCircuitBreaker(operation)
                ELSE
                    THROW CircuitOpenException("Circuit breaker is open")
                END IF

            CASE HalfOpen:
                TRY
                    result ← operation()
                    state.successCount ← state.successCount + 1

                    IF state.successCount >= HALF_OPEN_SUCCESS_THRESHOLD THEN
                        state.status ← Closed
                        state.failureCount ← 0
                        LOG("Circuit breaker closed after successful recovery")
                    END IF

                    RETURN result
                CATCH error
                    state.status ← Open
                    state.openedAt ← CurrentTime()
                    LOG("Circuit breaker reopened after failure in half-open state")
                    THROW error
                END TRY
        END SWITCH
    END FUNCTION
END
```

### Fallback Strategies

```
SUBROUTINE: ExecuteWithFallback
INPUT: primaryOperation, fallbackOperation
OUTPUT: result

BEGIN
    TRY
        result ← primaryOperation()
        RETURN result
    CATCH error AS e
        LOG_WARNING("Primary operation failed, attempting fallback", e)

        TRY
            result ← fallbackOperation()
            RETURN result
        CATCH fallbackError
            LOG_ERROR("Fallback also failed", fallbackError)
            THROW AggregateException([e, fallbackError])
        END TRY
    END TRY
END

EXAMPLES of Fallback Strategies:

// Cognee unavailable → use Zoho notes as fallback
SUBROUTINE: GetAccountContextWithFallback(accountId)
BEGIN
    TRY
        context ← MCP_COGNEE.retrieveContext(accountId)
        RETURN context
    CATCH
        LOG("Cognee unavailable, using Zoho notes as fallback")
        notes ← MCP_ZOHO.getNotes(accountId, limit: 50)
        context ← ConstructContextFromNotes(notes)
        RETURN context
    END TRY
END

// MCP tool unavailable → use REST API
SUBROUTINE: FetchAccountWithFallback(accountId)
BEGIN
    TRY
        account ← MCP_ZOHO.getAccount(accountId)
        RETURN account
    CATCH
        LOG("MCP unavailable, using REST API fallback")
        account ← ZohoRESTClient.getAccount(accountId)
        RETURN account
    END TRY
END
```

---

## Audit Trail Generation

### Algorithm: AuditLogger

```
ALGORITHM: LogAuditEvent
INPUT:
    sessionId (string)
    eventType (string)
    entityId (string)
    details (object)
OUTPUT:
    auditEntryId (string)

STRUCTURE: AuditEntry
    entryId: string (UUID)
    sessionId: string
    timestamp: timestamp
    eventType: string
    entityType: string
    entityId: string
    agentName: string (optional)
    userId: string (optional)
    action: string
    details: object
    dataReferences: List<DataReference>
    success: boolean
    errorMessage: string (optional)
END STRUCTURE

BEGIN
    entry ← new AuditEntry()
    entry.entryId ← GenerateUUID()
    entry.sessionId ← sessionId
    entry.timestamp ← CurrentTime()
    entry.eventType ← eventType
    entry.entityId ← entityId
    entry.details ← details

    // Extract metadata
    entry.agentName ← ExtractAgentName(details)
    entry.userId ← GetCurrentUser()
    entry.action ← DetermineAction(eventType, details)
    entry.success ← details.success OR true

    // Collect data references
    entry.dataReferences ← ExtractDataReferences(details)

    // Store in audit log
    TRY
        StoreAuditEntry(entry)

        // Also store in memory for session context
        Memory.store(
            "audit:" + sessionId + ":" + entry.entryId,
            entry,
            TTL: 7 days
        )

    CATCH error AS e
        // Audit logging failure is critical
        LOG_CRITICAL("Failed to store audit entry", entry.entryId, e)
        // Don't throw - continue operation but alert
        AlertOps("Audit logging failure", e)
    END TRY

    RETURN entry.entryId
END

SUBROUTINE: GenerateAuditReport
INPUT: session, auditLog
OUTPUT: AuditReport

BEGIN
    report ← new AuditReport()
    report.sessionId ← session.sessionId
    report.generatedAt ← CurrentTime()

    // Retrieve all audit entries for session
    entries ← RetrieveAuditEntries(session.sessionId)

    // Summary section
    report.summary ← new AuditSummary()
    report.summary.totalEvents ← entries.size
    report.summary.successfulEvents ← CountSuccessful(entries)
    report.summary.failedEvents ← entries.size - report.summary.successfulEvents
    report.summary.duration ← session.endTime - session.startTime

    // Breakdown by event type
    report.eventBreakdown ← GroupAndCount(entries, "eventType")

    // Agent activities
    report.agentActivities ← GroupByAgent(entries)

    // Data access log
    report.dataAccessed ← ExtractAllDataReferences(entries)

    // Error summary
    report.errors ← FilterFailedEntries(entries)

    // Recommendation trail
    report.recommendationTrail ← BuildRecommendationTrail(entries, session.recommendations)

    // Approval decisions
    report.approvalDecisions ← ExtractApprovalDecisions(entries)

    // Compliance checklist
    report.compliance ← VerifyComplianceRequirements(entries)

    RETURN report
END

SUBROUTINE: BuildRecommendationTrail
INPUT: entries, recommendations
OUTPUT: List<RecommendationTrail>

BEGIN
    trails ← []

    FOR EACH rec IN recommendations DO
        trail ← new RecommendationTrail()
        trail.recommendationId ← rec.recommendationId
        trail.accountId ← rec.accountId

        // Extract events related to this recommendation
        relatedEvents ← FilterEventsByEntity(entries, rec.recommendationId)

        // Build timeline
        timeline ← []
        FOR EACH event IN relatedEvents DO
            timeline.append({
                timestamp: event.timestamp,
                action: event.action,
                agent: event.agentName,
                details: event.details
            })
        END FOR

        trail.timeline ← timeline

        // Data sources used
        trail.dataSources ← ExtractDataSources(relatedEvents)

        // Decision rationale
        generationEvent ← FindEvent(relatedEvents, "RECOMMENDATION_GENERATED")
        IF generationEvent is not null THEN
            trail.rationale ← generationEvent.details.rationale
            trail.confidence ← generationEvent.details.confidence
        END IF

        // Approval status
        approvalEvent ← FindEvent(relatedEvents, "APPROVAL_DECISION")
        IF approvalEvent is not null THEN
            trail.approvalStatus ← approvalEvent.details.status
            trail.approvedBy ← approvalEvent.details.userId
            trail.approvedAt ← approvalEvent.timestamp
        END IF

        // Execution outcomes
        executionEvents ← FilterEvents(relatedEvents, "ACTION_EXECUTED")
        trail.executionOutcomes ← MapExecutionOutcomes(executionEvents)

        trails.append(trail)
    END FOR

    RETURN trails
END

SUBROUTINE: VerifyComplianceRequirements
INPUT: entries
OUTPUT: ComplianceChecklistResult

BEGIN
    checklist ← new ComplianceChecklistResult()

    // Requirement 1: All CRM writes must have approval
    writeEvents ← FilterEvents(entries, ["ACCOUNT_UPDATED", "TASK_CREATED", "EMAIL_SENT"])
    FOR EACH writeEvent IN writeEvents DO
        approvalExists ← HasPriorApproval(entries, writeEvent.entityId)
        IF NOT approvalExists THEN
            checklist.violations.append({
                requirement: "Approval Required for Writes",
                event: writeEvent.entryId,
                severity: Critical
            })
        END IF
    END FOR

    // Requirement 2: Sensitive data must be redacted in logs
    FOR EACH entry IN entries DO
        IF ContainsSensitiveData(entry.details) THEN
            checklist.violations.append({
                requirement: "Sensitive Data Redaction",
                event: entry.entryId,
                severity: High
            })
        END IF
    END FOR

    // Requirement 3: All data accesses must be logged
    dataAccessEvents ← FilterEvents(entries, "DATA_FETCH")
    expectedAccessCount ← EstimateExpectedDataAccesses(entries)
    IF dataAccessEvents.size < expectedAccessCount * 0.9 THEN
        checklist.warnings.append({
            requirement: "Complete Data Access Logging",
            message: "Some data accesses may not be logged",
            severity: Medium
        })
    END IF

    // Requirement 4: Audit trail must be immutable
    checksum ← CalculateAuditLogChecksum(entries)
    storedChecksum ← RetrieveStoredChecksum(entries[0].sessionId)
    IF checksum != storedChecksum THEN
        checklist.violations.append({
            requirement: "Audit Trail Immutability",
            message: "Audit log checksum mismatch detected",
            severity: Critical
        })
    END IF

    // Summary
    checklist.totalChecks ← 4
    checklist.passed ← 4 - checklist.violations.size
    checklist.compliant ← checklist.violations.isEmpty()

    RETURN checklist
END
```

---

## Session State Management

### Algorithm: SessionManager

```
ALGORITHM: CreateSession
INPUT: runConfig
OUTPUT: SessionState

BEGIN
    session ← new SessionState()
    session.sessionId ← "session-" + GenerateUUID()
    session.runType ← runConfig.runType
    session.startTime ← CurrentTime()
    session.status ← Running
    session.accountsProcessed ← 0
    session.accountsFailed ← 0
    session.recommendations ← []
    session.errors ← []
    session.metrics ← new PerformanceMetrics()

    // Store initial state
    PersistSession(session)

    // Initialize audit log
    LogAuditEvent(session.sessionId, "SESSION_STARTED", session.sessionId, {
        runType: runConfig.runType,
        configuration: runConfig
    })

    RETURN session
END

ALGORITHM: PersistSession
INPUT: session
OUTPUT: void

BEGIN
    // Store in multiple locations for reliability

    // 1. Local file system
    sessionPath ← ".swarm/sessions/" + session.sessionId + ".json"
    WriteToFile(sessionPath, SerializeJSON(session))

    // 2. Memory store (for quick access)
    Memory.store("session:" + session.sessionId, session, TTL: 7 days)

    // 3. Optional: external storage for long-term retention
    IF Config.persistentStorage.enabled THEN
        TRY
            UploadToExternalStorage(session)
        CATCH error
            LOG_WARNING("Failed to persist session to external storage", error)
            // Non-critical: continue
        END TRY
    END IF
END

ALGORITHM: RestoreSession
INPUT: sessionId
OUTPUT: SessionState or null

BEGIN
    // Try memory first (fastest)
    session ← Memory.retrieve("session:" + sessionId)
    IF session is not null THEN
        RETURN session
    END IF

    // Try local file system
    sessionPath ← ".swarm/sessions/" + sessionId + ".json"
    IF FileExists(sessionPath) THEN
        sessionData ← ReadFromFile(sessionPath)
        session ← DeserializeJSON(sessionData, SessionState)

        // Restore to memory
        Memory.store("session:" + sessionId, session, TTL: 7 days)

        RETURN session
    END IF

    // Try external storage
    IF Config.persistentStorage.enabled THEN
        TRY
            session ← DownloadFromExternalStorage(sessionId)
            IF session is not null THEN
                // Cache locally
                WriteToFile(sessionPath, SerializeJSON(session))
                Memory.store("session:" + sessionId, session, TTL: 7 days)
                RETURN session
            END IF
        CATCH error
            LOG_WARNING("Failed to restore session from external storage", error)
        END TRY
    END IF

    // Session not found
    RETURN null
END

ALGORITHM: UpdateSessionProgress
INPUT: session, update
OUTPUT: void

BEGIN
    // Apply update
    SWITCH update.type DO
        CASE "ACCOUNT_PROCESSED":
            session.accountsProcessed ← session.accountsProcessed + 1
            session.recommendations.extend(update.recommendations)

        CASE "ACCOUNT_FAILED":
            session.accountsFailed ← session.accountsFailed + 1
            session.errors.append(update.error)

        CASE "STATUS_CHANGE":
            session.status ← update.newStatus

        CASE "METRICS_UPDATE":
            session.metrics ← MergeMetrics(session.metrics, update.metrics)

        DEFAULT:
            LOG_WARNING("Unknown update type", update.type)
    END SWITCH

    // Update timestamp
    session.lastUpdated ← CurrentTime()

    // Persist updated state
    PersistSession(session)

    // Log update to audit trail
    LogAuditEvent(session.sessionId, "SESSION_UPDATED", session.sessionId, update)
END

ALGORITHM: CompleteSession
INPUT: session, outcome
OUTPUT: SessionState

BEGIN
    // Finalize status
    session.status ← outcome
    session.endTime ← CurrentTime()

    // Calculate final metrics
    session.metrics.totalDuration ← session.endTime - session.startTime
    session.metrics.avgAccountProcessingTime ←
        session.metrics.totalDuration / MAX(1, session.accountsProcessed)

    // Generate summary
    session.summary ← GenerateSessionSummary(session)

    // Persist final state
    PersistSession(session)

    // Log completion
    LogAuditEvent(session.sessionId, "SESSION_COMPLETED", session.sessionId, {
        outcome: outcome,
        duration: session.metrics.totalDuration,
        accountsProcessed: session.accountsProcessed,
        recommendationCount: session.recommendations.size
    })

    // Archive session (move to long-term storage)
    IF Config.archival.enabled THEN
        ArchiveSession(session)
    END IF

    RETURN session
END

SUBROUTINE: GenerateSessionSummary
INPUT: session
OUTPUT: SessionSummary

BEGIN
    summary ← new SessionSummary()

    // Basic stats
    summary.sessionId ← session.sessionId
    summary.duration ← session.endTime - session.startTime
    summary.accountsProcessed ← session.accountsProcessed
    summary.accountsFailed ← session.accountsFailed
    summary.successRate ←
        session.accountsProcessed / (session.accountsProcessed + session.accountsFailed)

    // Recommendation stats
    summary.totalRecommendations ← session.recommendations.size
    summary.byPriority ← CountByPriority(session.recommendations)
    summary.avgConfidence ← AverageConfidence(session.recommendations)

    // Top accounts
    summary.topAccounts ← ExtractTopAccounts(session.recommendations, 10)

    // Performance highlights
    summary.performance ← {
        avgProcessingTime: session.metrics.avgAccountProcessingTime,
        apiCalls: session.metrics.apiCallCount,
        cacheHitRate: session.metrics.cacheHitRate,
        tokenUsage: session.metrics.tokenUsage
    }

    // Error summary
    IF NOT session.errors.isEmpty() THEN
        summary.errorSummary ← {
            count: session.errors.size,
            byType: GroupErrors(session.errors),
            sampleErrors: session.errors.slice(0, 5)
        }
    END IF

    RETURN summary
END

ALGORITHM: CleanupOldSessions
INPUT: retentionPeriod (days)
OUTPUT: integer (count of cleaned sessions)

BEGIN
    cutoffDate ← CurrentTime() - (retentionPeriod * 24 hours)
    cleanedCount ← 0

    // List all session files
    sessionFiles ← ListFiles(".swarm/sessions/")

    FOR EACH sessionFile IN sessionFiles DO
        sessionData ← ReadFromFile(sessionFile)
        session ← DeserializeJSON(sessionData, SessionState)

        IF session.endTime < cutoffDate THEN
            // Archive if enabled, otherwise delete
            IF Config.archival.enabled THEN
                TRY
                    ArchiveSession(session)
                    DeleteFile(sessionFile)
                    cleanedCount ← cleanedCount + 1
                CATCH error
                    LOG_ERROR("Failed to archive session", session.sessionId, error)
                END TRY
            ELSE
                DeleteFile(sessionFile)
                cleanedCount ← cleanedCount + 1
            END IF
        END IF
    END FOR

    LOG("Cleaned up {count} old sessions", cleanedCount)

    RETURN cleanedCount
END
```

---

## Performance Optimization Strategies

### Caching Strategy

```
STRATEGY: Multi-Level Caching

Level 1: In-Memory Cache (Fastest)
- Account metadata
- Owner information
- Recently accessed data
- TTL: 5-10 minutes
- Eviction: LRU

Level 2: Session Cache (Scoped)
- Data used within current run
- Timeline events
- Insights and recommendations
- TTL: Duration of session
- Eviction: On session completion

Level 3: Persistent Cache (Long-term)
- Account change history
- Historical patterns
- Recommendation templates
- TTL: 6-24 hours
- Eviction: Size-based LRU

ALGORITHM: CachedDataFetch
INPUT: key, fetchFunction, ttl
OUTPUT: data

BEGIN
    // Check L1 cache
    data ← L1Cache.get(key)
    IF data is not null THEN
        RETURN data
    END IF

    // Check L2 cache
    data ← L2Cache.get(key)
    IF data is not null THEN
        L1Cache.set(key, data, ttl)  // Promote to L1
        RETURN data
    END IF

    // Check L3 cache
    data ← L3Cache.get(key)
    IF data is not null THEN
        L1Cache.set(key, data, ttl)
        L2Cache.set(key, data, SESSION_TTL)
        RETURN data
    END IF

    // Cache miss - fetch from source
    data ← fetchFunction()

    // Populate all cache levels
    L1Cache.set(key, data, ttl)
    L2Cache.set(key, data, SESSION_TTL)
    L3Cache.set(key, data, PERSISTENT_TTL)

    RETURN data
END
```

### Batch Processing Optimization

```
STRATEGY: Intelligent Batching

SUBROUTINE: OptimizeBatchProcessing
INPUT: accounts, maxConcurrency
OUTPUT: List<BatchGroup>

BEGIN
    // Group accounts by processing requirements
    groups ← []

    // Group 1: Critical accounts (process immediately)
    criticalAccounts ← FilterByPriority(accounts, [Critical, High])
    IF NOT criticalAccounts.isEmpty() THEN
        groups.append(BatchGroup(
            accounts: criticalAccounts,
            priority: 1,
            concurrency: maxConcurrency
        ))
    END IF

    // Group 2: Accounts with cached data (fast processing)
    cachedAccounts ← FilterByCacheAvailability(accounts)
    IF NOT cachedAccounts.isEmpty() THEN
        groups.append(BatchGroup(
            accounts: cachedAccounts,
            priority: 2,
            concurrency: maxConcurrency * 2  // Can process more in parallel
        ))
    END IF

    // Group 3: Standard accounts
    remainingAccounts ← accounts - criticalAccounts - cachedAccounts
    IF NOT remainingAccounts.isEmpty() THEN
        // Split into smaller batches to avoid timeout
        FOR EACH chunk IN ChunkList(remainingAccounts, 50) DO
            groups.append(BatchGroup(
                accounts: chunk,
                priority: 3,
                concurrency: maxConcurrency
            ))
        END FOR
    END IF

    RETURN groups
END
```

### API Call Optimization

```
STRATEGY: Minimize API Calls

1. Prefetch Related Data
   - When fetching account, also fetch deals, contacts, activities
   - Use MCP batch operations where available

2. Aggregate Queries
   - Combine multiple lookups into single query
   - Use filters to reduce data transfer

3. Incremental Sync
   - Only fetch changed data since last run
   - Store lastModified timestamps

4. Request Deduplication
   - Track in-flight requests
   - Return existing promise if same request made

ALGORITHM: DeduplicatedAPICall
INPUT: key, apiFunction
OUTPUT: data

STATIC: inFlightRequests (Map)

BEGIN
    // Check if request already in progress
    IF inFlightRequests.has(key) THEN
        LOG("Deduplicating request for {key}", key)
        RETURN AWAIT inFlightRequests.get(key)
    END IF

    // Create new request
    promise ← ASYNC apiFunction()
    inFlightRequests.set(key, promise)

    TRY
        data ← AWAIT promise
        RETURN data
    FINALLY
        inFlightRequests.delete(key)
    END TRY
END
```

### Parallel Execution Strategy

```
STRATEGY: Maximized Parallelism

SUBROUTINE: ParallelAgentExecution
INPUT: accountData
OUTPUT: results

BEGIN
    // Launch all agents in parallel, not sequential
    results ← PARALLEL_EXECUTE [
        DataScout.fetchDetails(accountData.accountId),
        MemoryAnalyst.analyzeHistory(accountData.accountId),
        PrecomputeRecommendationContext(accountData)
    ]

    // Results available simultaneously
    enrichedData ← results[0]
    historicalContext ← results[1]
    contextHints ← results[2]

    // Final synthesis can use all results
    recommendations ← RecommendationAuthor.generate(
        enrichedData,
        historicalContext,
        contextHints
    )

    RETURN recommendations
END

Time Complexity Improvement:
- Sequential: T_data + T_memory + T_context + T_recs
- Parallel: MAX(T_data, T_memory, T_context) + T_recs
- Speedup: ~2-3x for typical cases
```

### Memory Optimization

```
STRATEGY: Efficient Memory Usage

1. Streaming Processing
   - Don't load all accounts into memory
   - Process in batches
   - Release memory after each batch

2. Lazy Loading
   - Load timeline events on demand
   - Fetch insights only when needed

3. Data Pruning
   - Keep only essential fields
   - Remove redundant information
   - Compress large text fields

4. Resource Pooling
   - Reuse API clients
   - Connection pooling for database
   - Shared cache instances

ALGORITHM: StreamingAccountProcessor
INPUT: accountStream
OUTPUT: void

BEGIN
    batchAccumulator ← []

    FOR EACH account IN accountStream DO
        batchAccumulator.append(account)

        IF batchAccumulator.size >= BATCH_SIZE THEN
            ProcessBatch(batchAccumulator)
            batchAccumulator.clear()  // Release memory

            // Allow garbage collection
            ForceGarbageCollection() IF MemoryPressure > 80%
        END IF
    END FOR

    // Process remaining accounts
    IF NOT batchAccumulator.isEmpty() THEN
        ProcessBatch(batchAccumulator)
    END IF
END
```

---

## Complexity Analysis

### Time Complexity

**Main Orchestration Loop:**
```
Let:
- N = number of accounts
- B = batch size
- C = max concurrency
- A = number of agents per account

Per Account Processing:
- Data fetch: O(log M) where M = total CRM records (indexed lookup)
- Memory query: O(K) where K = timeline events (typically K ≈ 100)
- Recommendation generation: O(R) where R = candidate recommendations
- Total per account: O(log M + K + R)

Batch Processing:
- Sequential batches: (N / B) iterations
- Parallel within batch: min(B, C) concurrent operations
- Total: O((N / min(B,C)) * (log M + K + R))

With typical values (N=1000, B=50, C=10, M=100k, K=100, R=20):
- Per account: O(17 + 100 + 20) ≈ O(137)
- Total: O(1000/10 * 137) ≈ O(13,700) operations
- Wall clock: ~10-15 minutes (with API latency)

Optimizations reduce this to O(N/C * T_api) where T_api is dominated by
network latency, not computation.
```

**Zoho Data Scout:**
```
Single Account:
- Base fetch: O(1) with cache, O(log M) without
- Related data: O(D + A + N) for deals, activities, notes
- Change detection: O(F) where F = fields to compare
- Total: O(log M + D + A + N + F)

Typical: O(10 + 5 + 20 + 10 + 15) ≈ O(60)

With caching (80% hit rate):
- Average: 0.2 * O(60) + 0.8 * O(1) ≈ O(13)
```

**Memory Analyst:**
```
Timeline Retrieval:
- Cognee query: O(log T) where T = total stored events (indexed)
- Parse events: O(K) where K = returned events
- Sentiment analysis: O(K * S) where S = text processing time
- Engagement score: O(K)
- Total: O(log T + K + K*S + K) ≈ O(K*S)

With typical values (K=100, S=10ms):
- O(100 * 10) = O(1000) operations ≈ 1 second
```

**Recommendation Author:**
```
Rule-based generation:
- Analyze situation: O(F + I) for factors and insights
- Generate candidates: O(C) for candidate count
- Score candidates: O(C * V) for validation checks per candidate
- Rank: O(C log C) for sorting
- Enrich: O(R * D) for top R recommendations with D data points
- Total: O(F + I + C*V + C log C + R*D)

Typical (F=10, I=20, C=50, V=10, R=5, D=10):
- O(10 + 20 + 500 + 196 + 50) ≈ O(776)
```

### Space Complexity

**Session State:**
```
Per Session:
- Metadata: O(1)
- Recommendations: O(N * R) where N = accounts, R = recs per account
- Errors: O(E) where E = error count
- Audit log: O(L) where L = log entries
- Total: O(N*R + E + L)

With N=1000, R=5, E=50, L=5000:
- O(5000 + 50 + 5000) = O(10,050) records
- ~100 MB in memory (10KB per record)
```

**Cache Storage:**
```
L1 Cache (in-memory):
- Max entries: 1000
- Avg size: 5KB
- Total: ~5 MB

L2 Cache (session):
- Max entries: N (accounts in session)
- Avg size: 10KB
- Total: ~10-50 MB (for 1000-5000 accounts)

L3 Cache (persistent):
- Max entries: 10,000
- Avg size: 8KB
- Total: ~80 MB
- Eviction: LRU when >80MB

Total cache footprint: ~100-150 MB
```

**Audit Trail:**
```
Per Session:
- Audit entries: O(A * N) where A = actions per account
- Typical: 10 actions per account
- Storage: O(10 * N * E) where E = entry size

For N=1000, E=2KB:
- O(10,000 * 2KB) = 20 MB per session
- Compressed: ~5 MB
- Retention: 7 days = ~35 MB total (assuming 1 session/day)
```

### Scalability Targets

```
PERFORMANCE TARGETS:

Latency:
- Single account processing: <30 seconds (P95)
- Batch of 50 accounts: <2 minutes (P95)
- Full session (1000 accounts): <10 minutes (P95)
- Approval response time: <1 minute (after user action)

Throughput:
- Accounts per minute: 100-150 (with 10 concurrent)
- API calls per second: 5-10 (within Zoho rate limits)
- Recommendations per hour: 500-750

Resource Usage:
- Memory: <500 MB per session
- CPU: <50% avg during processing
- Network: <10 MB/min data transfer

Scalability:
- Accounts: Linear scaling to 10,000 accounts
- Owners: Support 100+ concurrent owners
- Recommendations: Generate 5,000+ per day
- Audit entries: Store 50,000+ per week
```

---

## Summary

This pseudocode document provides comprehensive algorithmic designs for the Sergas Super Account Manager Agent:

1. **Main Orchestration Loop**: Session management, queue-based processing, batch execution with concurrency control
2. **Zoho Data Scout**: Account fetching, enrichment, change detection with caching and retry logic
3. **Memory Analyst**: Timeline retrieval, insight generation, engagement scoring using Cognee
4. **Recommendation Author**: Multi-strategy recommendation generation with confidence scoring
5. **Approval Gate**: Human-in-the-loop confirmation across multiple channels
6. **Error Handling**: Retry logic, circuit breakers, fallback strategies
7. **Audit Trail**: Comprehensive logging, compliance verification, immutable trail
8. **Session State**: Persistence, restoration, progress tracking, cleanup
9. **Performance Optimization**: Multi-level caching, batching, parallelism, resource management
10. **Complexity Analysis**: Detailed time/space complexity with realistic performance targets

The algorithms are designed to be:
- **Fault-tolerant**: Graceful degradation, retry logic, fallback mechanisms
- **Auditable**: Complete trail of decisions and data access
- **Scalable**: Linear scaling to 10k accounts with optimized caching and parallelism
- **Secure**: Approval gates, data redaction, compliance verification
- **Performant**: <30s per account, <10min for 1000 accounts

These algorithms provide a clear blueprint for implementation in any programming language while maintaining the multi-agent architecture and integration requirements specified in the PRD.

---

**Next Phase**: Architecture design including technology stack, deployment model, and detailed component interactions.
