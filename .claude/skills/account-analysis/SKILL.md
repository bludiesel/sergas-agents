---
name: account-analysis
description: Account health analysis and risk detection for CRM systems. Use this skill when analyzing customer accounts, detecting at-risk accounts, identifying growth opportunities, calculating account health scores, tracking engagement patterns, and generating account insights. Essential for account managers, sales teams, and customer success operations.
---

# Account Analysis

## Overview

This skill provides comprehensive methodologies for analyzing customer accounts, detecting risks, identifying opportunities, and generating actionable insights. It combines CRM data analysis, behavioral pattern recognition, and predictive modeling to support data-driven account management.

## When to Use This Skill

Use this skill when:
- Analyzing account health and engagement status
- Detecting at-risk accounts requiring intervention
- Identifying expansion and upsell opportunities
- Calculating account scores and metrics
- Tracking account activity patterns over time
- Generating account briefings and summaries
- Prioritizing accounts for sales team attention
- Monitoring deal pipeline health

## Core Analysis Frameworks

### 1. Account Health Scoring

Calculate multi-dimensional health scores:

```python
def calculate_account_health_score(account_data: dict) -> dict:
    """
    Calculate comprehensive account health score

    Components:
    - Engagement (40%): Activity frequency, response rates
    - Financial (30%): Revenue, payment history, contract value
    - Satisfaction (20%): Support tickets, feedback scores
    - Strategic (10%): Strategic fit, growth potential
    """

    scores = {
        "engagement": calculate_engagement_score(account_data),
        "financial": calculate_financial_score(account_data),
        "satisfaction": calculate_satisfaction_score(account_data),
        "strategic": calculate_strategic_score(account_data)
    }

    # Weighted average
    weights = {
        "engagement": 0.40,
        "financial": 0.30,
        "satisfaction": 0.20,
        "strategic": 0.10
    }

    overall_score = sum(
        scores[key] * weights[key]
        for key in scores.keys()
    )

    return {
        "overall_score": overall_score,
        "component_scores": scores,
        "health_status": categorize_health(overall_score),
        "risk_level": assess_risk_level(scores)
    }
```

### 2. Risk Detection

Identify at-risk accounts using multiple signals:

```python
def detect_at_risk_accounts(account: dict) -> dict:
    """
    Detect multiple risk indicators

    Risk Signals:
    - Declining engagement (30+ days inactive)
    - Payment issues or contract near expiration
    - Negative support experiences
    - Executive turnover or org changes
    - Decreased product usage
    - Competitor activity
    """

    risk_indicators = []
    risk_score = 0

    # Engagement risk
    if account["days_since_last_contact"] > 30:
        risk_indicators.append({
            "type": "engagement",
            "severity": "high",
            "message": f"{account['days_since_last_contact']} days since last contact",
            "recommended_action": "Schedule check-in call"
        })
        risk_score += 30

    # Financial risk
    if account.get("days_until_contract_expiration", 999) < 60:
        risk_indicators.append({
            "type": "financial",
            "severity": "critical",
            "message": f"Contract expires in {account['days_until_contract_expiration']} days",
            "recommended_action": "Initiate renewal discussion"
        })
        risk_score += 40

    # Deal stagnation risk
    open_deals = account.get("open_deals", [])
    for deal in open_deals:
        if deal["days_in_stage"] > 45:
            risk_indicators.append({
                "type": "deal_stagnation",
                "severity": "medium",
                "message": f"Deal '{deal['name']}' stalled for {deal['days_in_stage']} days",
                "recommended_action": "Review deal obstacles with stakeholders"
            })
            risk_score += 15

    # Support ticket risk
    if account.get("open_critical_tickets", 0) > 0:
        risk_indicators.append({
            "type": "satisfaction",
            "severity": "high",
            "message": f"{account['open_critical_tickets']} critical support tickets open",
            "recommended_action": "Escalate support issues"
        })
        risk_score += 25

    return {
        "is_at_risk": risk_score > 50,
        "risk_score": min(risk_score, 100),
        "risk_level": categorize_risk(risk_score),
        "risk_indicators": risk_indicators,
        "priority": calculate_intervention_priority(risk_score, account)
    }
```

### 3. Opportunity Identification

Detect expansion and upsell opportunities:

```python
def identify_opportunities(account: dict, product_catalog: dict) -> list:
    """
    Identify expansion opportunities

    Signals:
    - High engagement with specific features
    - Usage approaching plan limits
    - Multiple departments using product
    - Positive satisfaction scores
    - Recent funding or growth
    - Successful case studies or testimonials
    """

    opportunities = []

    # Usage-based upsell
    if account.get("feature_usage_percent", 0) > 85:
        opportunities.append({
            "type": "capacity_expansion",
            "confidence": "high",
            "estimated_value": account["current_mrr"] * 0.30,
            "message": "Account approaching plan limits",
            "recommended_products": get_higher_tier_products(account),
            "talking_points": [
                "Current usage at 85% of plan capacity",
                "Upgrade prevents service disruptions",
                "Access to advanced features unlocked"
            ]
        })

    # Cross-sell opportunities
    unused_features = get_unused_features(account, product_catalog)
    if unused_features:
        opportunities.append({
            "type": "cross_sell",
            "confidence": "medium",
            "estimated_value": sum(f["price"] for f in unused_features),
            "message": f"{len(unused_features)} relevant features not yet adopted",
            "recommended_products": unused_features,
            "talking_points": [
                f"Based on industry ({account['industry']}), these features add value",
                "Similar customers see X% efficiency gains",
                "Easy to activate within current platform"
            ]
        })

    # Multi-buyer expansion
    if account.get("active_users", 0) > account.get("licensed_seats", 0) * 0.8:
        opportunities.append({
            "type": "seat_expansion",
            "confidence": "high",
            "estimated_value": (account["active_users"] - account["licensed_seats"]) * account["per_seat_price"],
            "message": "High seat utilization indicates need for expansion",
            "recommended_action": "Propose seat increase",
            "talking_points": [
                f"{account['active_users']} users active, {account['licensed_seats']} seats licensed",
                "Prevent access limitations for growing team",
                "Volume discount available for 10+ additional seats"
            ]
        })

    return opportunities
```

### 4. Activity Pattern Analysis

Track and analyze engagement patterns:

```python
def analyze_activity_patterns(account_history: list) -> dict:
    """
    Analyze temporal engagement patterns

    Metrics:
    - Activity frequency and consistency
    - Response time and responsiveness
    - Engagement channels (email, calls, meetings, product)
    - Stakeholder breadth (number of contacts engaged)
    - Content interests and topics discussed
    """

    from datetime import datetime, timedelta
    import pandas as pd

    # Convert to time series
    df = pd.DataFrame(account_history)
    df["date"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("date")

    # Calculate metrics
    analysis = {
        "total_interactions": len(df),
        "avg_interactions_per_week": len(df) / ((df.index.max() - df.index.min()).days / 7),
        "last_interaction_date": df.index.max().isoformat(),
        "days_since_last_interaction": (datetime.now() - df.index.max()).days,
        "engagement_trend": calculate_trend(df),
        "primary_channels": df["channel"].value_counts().to_dict(),
        "active_contacts": df["contact_name"].nunique(),
        "topic_distribution": df["topic"].value_counts().to_dict()
    }

    # Detect patterns
    analysis["patterns"] = {
        "is_declining": analysis["engagement_trend"] < -0.2,
        "is_growing": analysis["engagement_trend"] > 0.2,
        "is_consistent": abs(analysis["engagement_trend"]) < 0.2,
        "has_gone_quiet": analysis["days_since_last_interaction"] > 30,
        "multi_stakeholder": analysis["active_contacts"] > 3
    }

    return analysis
```

## Account Briefing Generation

### Comprehensive Account Brief

```python
async def generate_account_brief(
    account_id: str,
    zoho_client,
    cognee_client
) -> dict:
    """
    Generate comprehensive account briefing

    Sections:
    1. Executive Summary
    2. Account Health & Risk Assessment
    3. Recent Activity Summary
    4. Open Deals & Pipeline Status
    5. Opportunities & Recommendations
    6. Next Actions
    """

    # Gather data from multiple sources
    account = await zoho_client.get_account(account_id)
    contacts = await zoho_client.get_contacts(account_id)
    deals = await zoho_client.get_deals(account_id)
    activities = await zoho_client.get_activities(account_id)
    historical_context = await cognee_client.search_account_history(account_id)

    # Perform analyses
    health_score = calculate_account_health_score({
        "account": account,
        "contacts": contacts,
        "deals": deals,
        "activities": activities
    })

    risk_assessment = detect_at_risk_accounts({
        "account": account,
        "activities": activities,
        "deals": deals
    })

    opportunities = identify_opportunities(account, product_catalog)

    activity_patterns = analyze_activity_patterns(activities)

    # Generate brief
    brief = {
        "account_id": account_id,
        "account_name": account["Account_Name"],
        "owner": account["Owner"]["name"],
        "generated_at": datetime.now().isoformat(),

        "executive_summary": {
            "health_status": health_score["health_status"],
            "overall_score": health_score["overall_score"],
            "risk_level": risk_assessment["risk_level"],
            "key_highlights": generate_highlights(account, health_score, risk_assessment)
        },

        "health_assessment": health_score,

        "risk_assessment": risk_assessment,

        "recent_activity": {
            "last_contact": activity_patterns["last_interaction_date"],
            "days_since_contact": activity_patterns["days_since_last_interaction"],
            "total_interactions_30d": activity_patterns["total_interactions"],
            "engagement_trend": activity_patterns["engagement_trend"],
            "patterns": activity_patterns["patterns"]
        },

        "open_deals": [
            {
                "name": deal["Deal_Name"],
                "stage": deal["Stage"],
                "amount": deal["Amount"],
                "close_date": deal["Closing_Date"],
                "days_in_stage": deal["days_in_stage"],
                "stagnation_risk": deal["days_in_stage"] > 45
            }
            for deal in deals if deal["Stage"] != "Closed Won"
        ],

        "opportunities": opportunities,

        "recommendations": generate_recommendations(
            health_score,
            risk_assessment,
            opportunities,
            activity_patterns
        ),

        "next_actions": prioritize_next_actions(
            risk_assessment["risk_indicators"],
            opportunities,
            activity_patterns
        )
    }

    return brief
```

### Recommendation Engine

```python
def generate_recommendations(
    health_score: dict,
    risk_assessment: dict,
    opportunities: list,
    activity_patterns: dict
) -> list:
    """
    Generate prioritized, actionable recommendations

    Recommendation Types:
    - Risk mitigation actions
    - Engagement improvement tactics
    - Opportunity pursuit strategies
    - Relationship building activities
    """

    recommendations = []

    # Risk-based recommendations
    if risk_assessment["is_at_risk"]:
        for indicator in risk_assessment["risk_indicators"]:
            recommendations.append({
                "priority": "critical" if indicator["severity"] == "critical" else "high",
                "category": "risk_mitigation",
                "action": indicator["recommended_action"],
                "rationale": indicator["message"],
                "urgency": calculate_urgency(indicator),
                "estimated_effort": "1-2 hours",
                "expected_outcome": f"Reduce {indicator['type']} risk"
            })

    # Engagement recommendations
    if activity_patterns["days_since_last_interaction"] > 14:
        recommendations.append({
            "priority": "high",
            "category": "engagement",
            "action": "Schedule check-in call or send personalized email",
            "rationale": f"{activity_patterns['days_since_last_interaction']} days since last contact",
            "urgency": "next 7 days",
            "estimated_effort": "30 minutes",
            "expected_outcome": "Re-establish communication rhythm"
        })

    # Opportunity recommendations
    for opp in opportunities:
        recommendations.append({
            "priority": "medium",
            "category": "opportunity",
            "action": f"Present {opp['type']} opportunity",
            "rationale": opp["message"],
            "urgency": "next 30 days",
            "estimated_effort": "1-2 hours",
            "expected_outcome": f"Potential ${opp['estimated_value']:,.0f} expansion",
            "talking_points": opp.get("talking_points", [])
        })

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recommendations.sort(key=lambda x: priority_order[x["priority"]])

    return recommendations
```

## Integration with Agent Workflows

### Subagent Configuration

```python
# Account Analyst subagent
analyst_config = {
    "name": "Account Analyst",
    "system_prompt": """
    You are an Account Analyst specialized in CRM data analysis.

    Your responsibilities:
    1. Calculate account health scores
    2. Detect at-risk accounts
    3. Identify expansion opportunities
    4. Analyze activity patterns
    5. Generate actionable insights

    Always provide:
    - Quantitative metrics and scores
    - Clear rationale for assessments
    - Specific, actionable recommendations
    - Risk levels and urgency indicators

    Base all analyses on data, not assumptions.
    """,
    "allowed_tools": [
        "Read",
        "get_contact_by_email_tool",
        "get_deal_by_name_tool",
        "list_open_deals_tool",
        "search_account_history"
    ]
}
```

## Best Practices

1. **Multi-Signal Analysis**
   - Combine quantitative metrics with qualitative insights
   - Use multiple data sources (CRM, product usage, support, billing)
   - Validate signals against historical patterns

2. **Temporal Context**
   - Always include time-series analysis
   - Compare current state to baselines and trends
   - Account for seasonal patterns and business cycles

3. **Stakeholder Awareness**
   - Track engagement breadth (single vs. multi-stakeholder)
   - Identify champions, detractors, and economic buyers
   - Monitor org changes and personnel turnover

4. **Actionability**
   - Every insight should lead to a specific action
   - Prioritize recommendations by impact and effort
   - Include talking points and next-step guidance

5. **Continuous Learning**
   - Track recommendation acceptance rates
   - Measure outcome effectiveness
   - Refine scoring models based on results

## Resources

See `references/api_reference.md` for:
- Detailed scoring algorithms
- Risk model parameters
- Opportunity detection criteria
- Pattern analysis examples

See `scripts/` for:
- Account scoring calculators
- Risk detection utilities
- Report generation templates
