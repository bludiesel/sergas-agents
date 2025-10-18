---
name: zoho-crm-analysis
description: Advanced Zoho CRM analysis for account health scoring, risk detection, and engagement patterns. Use when analyzing Zoho CRM accounts, detecting at-risk customers, identifying growth opportunities, or generating account insights for account managers and sales teams.
license: MIT
---

# Zoho CRM Analysis - Account Intelligence & Risk Detection

Comprehensive Zoho CRM analysis skill for account health monitoring, risk detection, and opportunity identification in customer success and account management workflows.

## When to Use

- Analyzing account health and engagement patterns
- Detecting at-risk accounts requiring intervention
- Identifying upsell and cross-sell opportunities
- Generating account executive insights and recommendations
- Calculating account health scores
- Tracking account lifecycle stages
- Monitoring customer engagement metrics

## Core Workflow

### Phase 1: Data Collection

1. **Retrieve Account Data** using Zoho CRM MCP tools or API:
   - Account details (company, industry, size, ARR)
   - Contact information and roles
   - Deal history and pipeline
   - Activity logs (calls, emails, meetings)
   - Support tickets and issues
   - Product usage data

2. **Gather Historical Context** using Cognee memory:
   - Previous health scores
   - Past interventions and outcomes
   - Communication history
   - Relationship timeline
   - Success patterns

### Phase 2: Health Score Calculation

Calculate comprehensive account health score (0-100) based on:

**Engagement Score (40% weight)**:
- Communication frequency (20%)
- Response time and quality (10%)
- Meeting attendance (5%)
- Product adoption rate (5%)

**Financial Score (30% weight)**:
- Revenue trend (15%)
- Payment history (10%)
- Contract renewal status (5%)

**Relationship Score (20% weight)**:
- Executive sponsor engagement (10%)
- Stakeholder breadth (5%)
- Champion presence (5%)

**Risk Score (10% weight)** - Negative indicators:
- Support ticket volume (5%)
- Churn signals (3%)
- Competitive activity (2%)

**Scoring Formula**:
```
Health Score = (Engagement * 0.4) + (Financial * 0.3) + (Relationship * 0.2) - (Risk * 0.1)

Ranges:
- 80-100: Healthy (Green)
- 60-79: At Risk (Yellow)
- 0-59: Critical (Red)
```

### Phase 3: Risk Detection

Identify risk patterns using these signals:

**Critical Risk Signals** (Immediate action required):
- No executive engagement in 60+ days
- Declining product usage (>30% drop)
- Multiple escalated support tickets
- Payment delays or disputes
- Competitor mentions in communications
- Non-renewal communication
- Key stakeholder departure

**Warning Signals** (Monitor closely):
- Decreased meeting attendance
- Slow response times
- Budget cuts or restructuring
- Product adoption plateaus
- Single point of contact risk
- Contract approaching renewal (<90 days)

**Opportunity Signals** (Growth potential):
- Increasing usage trends
- New stakeholder engagement
- Positive feedback and testimonials
- Expansion discussions
- Budget increase mentions
- Referral requests

### Phase 4: Pattern Analysis

Analyze engagement patterns across:

**Time-Based Patterns**:
- Weekly/monthly activity trends
- Seasonal variations
- Lifecycle stage progression
- Touchpoint frequency

**Behavioral Patterns**:
- Communication channel preferences
- Response time consistency
- Meeting patterns
- Product usage patterns

**Relationship Patterns**:
- Stakeholder engagement distribution
- Decision-maker accessibility
- Champion effectiveness
- Cross-functional engagement

### Phase 5: Insight Generation

Generate actionable insights:

**Account Summary**:
- Current health score with trend
- Risk level and primary concerns
- Opportunity assessment
- Recommended actions

**Key Metrics**:
- Days since last contact
- Active deals and pipeline value
- Support ticket resolution rate
- Product adoption percentage
- Contract renewal date and status

**Recommended Actions** (Priority-ranked):
1. Immediate interventions for critical risks
2. Strategic initiatives for at-risk accounts
3. Growth strategies for healthy accounts
4. Maintenance activities for stable accounts

**Communication Suggestions**:
- Personalized outreach templates
- Meeting agenda recommendations
- Value reinforcement messaging
- Executive business review topics

### Phase 6: Reporting & Storage

**Generate Reports**:
- Executive dashboard view
- Detailed account analysis
- Risk assessment summary
- Action plan with timelines

**Store in Memory** (Cognee):
- Health score history
- Risk detection outcomes
- Intervention effectiveness
- Pattern recognition data
- Best practices learned

## Analysis Dimensions

### Financial Health

**Metrics to Analyze**:
- Annual Recurring Revenue (ARR)
- Customer Lifetime Value (CLV)
- Revenue growth rate
- Payment history
- Contract terms and renewal date
- Upsell/cross-sell potential

**Risk Indicators**:
- Declining revenue
- Payment delays
- Downgrade requests
- Budget cuts
- Procurement changes

### Engagement Health

**Metrics to Analyze**:
- Communication frequency (calls, emails, meetings)
- Response time averages
- Meeting attendance rate
- Product login frequency
- Feature adoption rate
- Training participation

**Risk Indicators**:
- Communication gaps (>14 days)
- Declining meeting attendance
- Slow response times (>48 hours)
- Decreased product usage
- Ignored outreach attempts

### Relationship Health

**Metrics to Analyze**:
- Executive sponsor presence
- Stakeholder count and roles
- Champion effectiveness
- Multi-threading score
- Decision-maker access
- Cross-functional relationships

**Risk Indicators**:
- Single point of contact
- Champion departure
- Stakeholder churn
- Executive disengagement
- Gatekeeper barriers

### Product Health

**Metrics to Analyze**:
- Active users vs. licenses
- Feature adoption rate
- Usage frequency
- Integration completeness
- Training completion
- Support ticket trends

**Risk Indicators**:
- Low adoption rate
- Unused features
- Incomplete implementation
- Frequent support issues
- Training non-completion

## Integration Points

### Zoho CRM MCP Tools

Use these MCP tools for data retrieval:

```bash
# Get account details
mcp__zoho-crm__get_account --account_id="[id]"

# Search for contacts
mcp__zoho-crm__search_contacts --account_id="[id]"

# Get deals
mcp__zoho-crm__get_deals --account_id="[id]"

# Get activities
mcp__zoho-crm__get_activities --account_id="[id]" --type="all"

# Get notes
mcp__zoho-crm__get_notes --related_id="[id]" --related_module="Accounts"
```

### Cognee Memory Integration

Store and retrieve analysis data:

```bash
# Store health score
npx cognee memory store "account/[id]/health_score" --data="[score_data]"

# Retrieve historical patterns
npx cognee memory retrieve "account/[id]/patterns"

# Store risk detection
npx cognee memory store "account/[id]/risk_assessment" --data="[risk_data]"

# Search similar patterns
npx cognee memory search "accounts with similar risk patterns"
```

### Recommendation Engine

Generate next-best-actions:

```bash
# Generate recommendations based on health score
npx generate-recommendations --account_id="[id]" --health_score="[score]"

# Create action plan
npx create-action-plan --account_id="[id]" --priority="high"
```

## Best Practices

### Data Quality

✅ **Do**:
- Verify data completeness before analysis
- Cross-reference multiple data sources
- Validate anomalies with historical context
- Consider data freshness and relevance
- Account for seasonality and business cycles

❌ **Don't**:
- Rely on incomplete data for scoring
- Ignore missing critical information
- Make assumptions without validation
- Overlook data quality issues
- Skip historical context review

### Scoring Methodology

✅ **Do**:
- Use weighted scoring for different dimensions
- Account for industry-specific patterns
- Adjust scores based on lifecycle stage
- Consider company size and segment
- Include qualitative signals

❌ **Don't**:
- Use one-size-fits-all scoring
- Ignore context and nuance
- Over-rely on automated scores
- Neglect human judgment
- Skip score validation

### Risk Detection

✅ **Do**:
- Monitor multiple risk indicators
- Detect patterns early
- Prioritize by severity and urgency
- Validate with account team
- Document risk history

❌ **Don't**:
- React to single data points
- Ignore warning signals
- Delay intervention on critical risks
- Assume risk will self-resolve
- Skip root cause analysis

### Actionability

✅ **Do**:
- Provide specific, actionable recommendations
- Prioritize by impact and effort
- Include timeline and ownership
- Suggest concrete next steps
- Offer communication templates

❌ **Don't**:
- Give vague or generic advice
- Overwhelm with too many actions
- Ignore implementation constraints
- Skip prioritization
- Lack follow-up mechanisms

## Output Formats

### Executive Summary

```markdown
# Account Health Report: [Company Name]

**Health Score**: [Score]/100 ([Trend])
**Risk Level**: [Green/Yellow/Red]
**Last Contact**: [Days] days ago
**Next Renewal**: [Date] ([Days] days)

## Key Findings
- [Finding 1]
- [Finding 2]
- [Finding 3]

## Recommended Actions
1. [Priority 1 Action] - [Owner] - [Timeline]
2. [Priority 2 Action] - [Owner] - [Timeline]
3. [Priority 3 Action] - [Owner] - [Timeline]
```

### Detailed Analysis

```markdown
# Comprehensive Account Analysis: [Company Name]

## Health Score Breakdown

### Engagement Score: [Score]/40
- Communication Frequency: [Score]/20
- Response Quality: [Score]/10
- Meeting Attendance: [Score]/5
- Product Adoption: [Score]/5

### Financial Score: [Score]/30
- Revenue Trend: [Score]/15
- Payment History: [Score]/10
- Renewal Status: [Score]/5

### Relationship Score: [Score]/20
- Executive Engagement: [Score]/10
- Stakeholder Breadth: [Score]/5
- Champion Presence: [Score]/5

### Risk Score: [Score]/10 (negative)
- Support Issues: [Score]/5
- Churn Signals: [Score]/3
- Competitive Activity: [Score]/2

## Risk Assessment

### Critical Risks
- [Risk 1]: [Description and impact]
- [Risk 2]: [Description and impact]

### Warning Signals
- [Signal 1]: [Description and recommendation]
- [Signal 2]: [Description and recommendation]

### Opportunities
- [Opportunity 1]: [Description and potential value]
- [Opportunity 2]: [Description and potential value]

## Engagement Pattern Analysis

**Communication Trends**: [Analysis]
**Product Usage**: [Analysis]
**Relationship Depth**: [Analysis]

## Recommended Action Plan

### Immediate Actions (This Week)
1. [Action]: [Description] - [Owner] - [Due]

### Short-term Actions (This Month)
1. [Action]: [Description] - [Owner] - [Due]

### Strategic Actions (This Quarter)
1. [Action]: [Description] - [Owner] - [Due]
```

## Advanced Use Cases

### Portfolio Analysis

Analyze multiple accounts to identify trends:

1. Calculate health scores for entire portfolio
2. Segment by health score ranges
3. Identify common risk patterns
4. Prioritize intervention resources
5. Forecast churn risk at portfolio level

### Predictive Modeling

Use historical data for predictions:

1. Analyze past churn events
2. Identify leading indicators
3. Build risk prediction models
4. Score accounts by churn probability
5. Generate early warning alerts

### Benchmarking

Compare accounts against peers:

1. Define peer groups (industry, size, segment)
2. Calculate average metrics
3. Identify outliers
4. Determine best practices
5. Set improvement targets

### Cohort Analysis

Track account cohorts over time:

1. Group accounts by signup period
2. Track health score progression
3. Identify lifecycle patterns
4. Measure retention rates
5. Optimize onboarding and engagement

## Integration with Other Skills

**account-analysis**: Foundation for health scoring
**recommendation-engine**: Action plan generation
**cognee-memory-management**: Historical context and pattern storage
**zoho-crm-integration**: Data retrieval and updates
**agent-orchestration**: Workflow coordination

## Troubleshooting

**Incomplete data**:
→ Use multiple data sources
→ Request missing information from account team
→ Document data gaps in analysis

**Conflicting signals**:
→ Weight by recency and reliability
→ Validate with qualitative context
→ Consult with account owner

**Unclear risk level**:
→ Review multiple risk indicators
→ Consider historical patterns
→ Escalate borderline cases for human judgment

**Low confidence scores**:
→ Gather more data points
→ Extend analysis time period
→ Incorporate qualitative insights

## Metrics to Track

**Analysis Quality**:
- Accuracy of risk predictions
- False positive/negative rates
- Intervention success rates
- Early detection effectiveness

**Business Impact**:
- Churn prevention rate
- Upsell identification accuracy
- Account health improvement
- ROI of interventions

## Related Resources

- Zoho CRM Python SDK documentation
- Cognee memory management patterns
- Account health scoring methodologies
- Customer success best practices
- Risk detection frameworks
