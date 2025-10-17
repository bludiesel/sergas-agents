---
name: recommendation-engine
description: Actionable recommendation generation for account management and sales workflows. Use this skill when generating next-best-actions for account executives, creating follow-up strategies, drafting customer communications, prioritizing tasks, and producing decision support insights. Essential for AI-assisted account management, sales automation, and customer success operations.
---

# Recommendation Engine

## Overview

This skill provides frameworks for generating intelligent, actionable recommendations for account management workflows. It covers recommendation types, prioritization methods, confidence scoring, and integration patterns for multi-agent systems.

## When to Use This Skill

Use this skill when:
- Generating next-best-action recommendations for account owners
- Creating follow-up task suggestions based on account status
- Drafting customer email templates and communication strategies
- Prioritizing account owner workload and activities
- Producing decision support for complex account situations
- Automating workflow suggestions based on triggers
- Creating escalation recommendations

## Recommendation Taxonomy

### 1. Risk Mitigation Actions

Recommendations to address at-risk accounts:

```python
RISK_MITIGATION_TEMPLATES = {
    "contract_expiration": {
        "trigger": "days_until_expiration < 60",
        "action": "Initiate renewal discussion",
        "template": """
Subject: Let's discuss your {product_name} renewal

Hi {contact_name},

I wanted to reach out as your {product_name} contract is up for renewal on {expiration_date}.

Over the past {contract_duration}, you've achieved:
{list_achievements}

I'd love to schedule time to discuss your renewal and how we can continue supporting your goals for {next_year}.

Would you be available for a brief call next week?

Best regards,
{owner_name}
        """,
        "urgency": "high",
        "estimated_effort": "30 minutes",
        "success_criteria": "Renewal meeting scheduled within 14 days"
    },

    "engagement_decline": {
        "trigger": "days_since_last_contact > 30",
        "action": "Re-engage with value-add touchpoint",
        "template": """
Subject: Thought this might interest you

Hi {contact_name},

It's been a while since we last connected. I came across {relevant_resource} and immediately thought of you given {specific_reason}.

{brief_value_proposition}

Would love to hear how things are going with {their_initiative}. Any time for a quick catch-up call?

Best,
{owner_name}
        """,
        "urgency": "medium",
        "estimated_effort": "20 minutes",
        "success_criteria": "Response received or meeting scheduled"
    },

    "deal_stagnation": {
        "trigger": "deal.days_in_stage > 45",
        "action": "Diagnose and address deal blockers",
        "template": """
Subject: Moving {deal_name} forward

Hi {contact_name},

I wanted to check in on {deal_name}. It's been {days_in_stage} days since we last discussed this.

Are there any obstacles or concerns we should address? I'm here to help remove any blockers.

Potential next steps:
{list_next_steps}

When would be a good time to discuss?

Best,
{owner_name}
        """,
        "urgency": "high",
        "estimated_effort": "1 hour",
        "success_criteria": "Deal advances to next stage or clear path forward established"
    }
}
```

### 2. Opportunity Pursuit Actions

Recommendations for growth and expansion:

```python
OPPORTUNITY_PURSUIT_TEMPLATES = {
    "capacity_expansion": {
        "trigger": "usage_percent > 85",
        "action": "Propose plan upgrade",
        "template": """
Subject: Let's discuss your {product_name} capacity

Hi {contact_name},

I noticed your team is currently using {usage_percent}% of your {current_plan} capacity. That's great to see such strong adoption!

To ensure uninterrupted service and unlock additional features, I'd recommend considering our {recommended_plan}:

Benefits:
{list_upgrade_benefits}

The upgrade would cost an additional ${monthly_increase}/month and can be activated immediately.

Would you like to discuss this week?

Best,
{owner_name}
        """,
        "urgency": "medium",
        "estimated_effort": "30 minutes",
        "expected_value": "${monthly_increase} MRR",
        "success_criteria": "Upgrade proposal presented and decision obtained"
    },

    "cross_sell": {
        "trigger": "unused_relevant_features > 0",
        "action": "Introduce complementary products",
        "template": """
Subject: Enhancing your {current_product} experience

Hi {contact_name},

Given your team's success with {current_product}, I wanted to share how {complementary_product} could add even more value.

I've seen similar companies in {industry} achieve:
{list_customer_outcomes}

The setup takes less than a day, and we can have you seeing results within a week.

Are you interested in a brief demo?

Best,
{owner_name}
        """,
        "urgency": "low",
        "estimated_effort": "1 hour",
        "expected_value": "${addon_price} MRR",
        "success_criteria": "Demo scheduled or trial initiated"
    }
}
```

### 3. Relationship Building Actions

Recommendations for strengthening customer relationships:

```python
RELATIONSHIP_BUILDING_TEMPLATES = {
    "executive_introduction": {
        "trigger": "account_value > threshold AND no_executive_contact",
        "action": "Facilitate executive connection",
        "template": """
Subject: Introduction to {exec_name}, our {exec_title}

Hi {contact_name},

Given the strategic partnership between {customer_company} and {our_company}, I'd like to introduce you to {exec_name}, our {exec_title}.

{exec_name} oversees {exec_responsibilities} and is passionate about helping customers like you achieve {customer_goals}.

Would you be open to a brief introductory call? {exec_name} is available {suggested_times}.

Best,
{owner_name}
        """,
        "urgency": "low",
        "estimated_effort": "30 minutes",
        "success_criteria": "Executive introduction completed"
    },

    "business_review": {
        "trigger": "months_since_qbr > 3",
        "action": "Schedule quarterly business review",
        "template": """
Subject: Q{quarter} Business Review for {customer_company}

Hi {contact_name},

I'd like to schedule our Q{quarter} business review to discuss:

1. Progress against your goals set in our last review
2. Key metrics and ROI from {product_name}
3. Opportunities to optimize your implementation
4. Roadmap preview and upcoming features

I'll prepare a comprehensive report beforehand. Would {suggested_date_1} or {suggested_date_2} work for a 45-minute call?

Best,
{owner_name}
        """,
        "urgency": "medium",
        "estimated_effort": "2 hours (prep + meeting)",
        "success_criteria": "QBR completed with documented outcomes"
    }
}
```

## Recommendation Generation Engine

### Core Recommendation Algorithm

```python
async def generate_recommendations(
    account_data: dict,
    health_assessment: dict,
    risk_indicators: list,
    opportunities: list,
    activity_history: list,
    owner_preferences: dict = None
) -> list:
    """
    Generate prioritized, contextualized recommendations

    Process:
    1. Analyze account state and identify triggers
    2. Generate candidate recommendations
    3. Score recommendations by impact, effort, confidence
    4. Contextualize with account history and patterns
    5. Prioritize and rank
    6. Format for consumption
    """

    recommendations = []

    # Generate risk mitigation recommendations
    for indicator in risk_indicators:
        if indicator["severity"] in ["critical", "high"]:
            rec = generate_risk_mitigation_rec(indicator, account_data)
            recommendations.append(rec)

    # Generate opportunity recommendations
    for opp in opportunities:
        if opp["confidence"] in ["high", "medium"]:
            rec = generate_opportunity_rec(opp, account_data)
            recommendations.append(rec)

    # Generate relationship recommendations
    relationship_recs = generate_relationship_recs(
        account_data,
        activity_history
    )
    recommendations.extend(relationship_recs)

    # Score and prioritize
    for rec in recommendations:
        rec["score"] = calculate_recommendation_score(
            rec,
            account_data,
            owner_preferences
        )

    # Sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    # Add context and formatting
    for rec in recommendations:
        rec["context"] = generate_recommendation_context(
            rec,
            account_data,
            activity_history
        )
        rec["formatted_output"] = format_recommendation(rec)

    return recommendations
```

### Recommendation Scoring

```python
def calculate_recommendation_score(
    recommendation: dict,
    account_data: dict,
    owner_preferences: dict = None
) -> float:
    """
    Multi-factor scoring: impact × confidence × urgency / effort

    Factors:
    - Expected impact (revenue, retention, relationship)
    - Confidence level
    - Urgency (time sensitivity)
    - Effort required
    - Owner preferences/style
    - Historical success rate
    """

    # Base factors
    impact = recommendation.get("expected_impact", 5)  # 1-10 scale
    confidence = recommendation.get("confidence_score", 0.7)  # 0-1 scale
    urgency = recommendation.get("urgency_score", 5)  # 1-10 scale
    effort = recommendation.get("effort_hours", 1)  # hours

    # Calculate base score
    base_score = (impact * confidence * urgency) / max(effort, 0.5)

    # Adjust for account value
    account_value_multiplier = 1.0
    if account_data.get("annual_revenue", 0) > 100000:
        account_value_multiplier = 1.5
    elif account_data.get("annual_revenue", 0) > 50000:
        account_value_multiplier = 1.2

    # Adjust for risk level
    risk_multiplier = 1.0
    if recommendation["category"] == "risk_mitigation":
        risk_level = account_data.get("risk_level", "low")
        risk_multipliers = {"critical": 2.0, "high": 1.5, "medium": 1.2, "low": 1.0}
        risk_multiplier = risk_multipliers.get(risk_level, 1.0)

    # Adjust for owner preferences
    preference_multiplier = 1.0
    if owner_preferences:
        pref_category = owner_preferences.get("preferred_categories", [])
        if recommendation["category"] in pref_category:
            preference_multiplier = 1.3

    # Final score
    score = (
        base_score *
        account_value_multiplier *
        risk_multiplier *
        preference_multiplier
    )

    return round(score, 2)
```

### Confidence Assessment

```python
def calculate_confidence_score(
    recommendation: dict,
    account_history: list,
    similar_accounts: list = None
) -> float:
    """
    Assess confidence in recommendation success

    Factors:
    - Data completeness
    - Historical pattern strength
    - Similar account outcomes
    - Stakeholder engagement level
    - Timing appropriateness
    """

    confidence_factors = {
        "data_quality": assess_data_quality(account_history),
        "pattern_strength": assess_pattern_strength(account_history),
        "historical_success": assess_historical_success(
            recommendation["action_type"],
            similar_accounts
        ),
        "timing": assess_timing_appropriateness(
            recommendation,
            account_history
        ),
        "stakeholder_readiness": assess_stakeholder_readiness(
            recommendation,
            account_history
        )
    }

    # Weighted average
    weights = {
        "data_quality": 0.20,
        "pattern_strength": 0.25,
        "historical_success": 0.30,
        "timing": 0.15,
        "stakeholder_readiness": 0.10
    }

    confidence = sum(
        confidence_factors[key] * weights[key]
        for key in confidence_factors.keys()
    )

    return confidence
```

## Output Formatting

### Human-Readable Brief Format

```python
def format_recommendation_brief(recommendations: list) -> str:
    """
    Format recommendations for account owner consumption
    """

    output = []
    output.append("=" * 60)
    output.append("RECOMMENDED ACTIONS")
    output.append("=" * 60)
    output.append("")

    # Group by priority
    by_priority = {
        "Critical": [r for r in recommendations if r["priority"] == "critical"],
        "High": [r for r in recommendations if r["priority"] == "high"],
        "Medium": [r for r in recommendations if r["priority"] == "medium"]
    }

    for priority_level, recs in by_priority.items():
        if not recs:
            continue

        output.append(f"{priority_level} Priority ({len(recs)} actions)")
        output.append("-" * 60)

        for i, rec in enumerate(recs, 1):
            output.append(f"{i}. {rec['action']}")
            output.append(f"   Category: {rec['category']}")
            output.append(f"   Rationale: {rec['rationale']}")
            output.append(f"   Effort: {rec['estimated_effort']}")
            output.append(f"   Timeline: {rec['urgency']}")

            if rec.get("expected_value"):
                output.append(f"   Expected Value: {rec['expected_value']}")

            if rec.get("draft_message"):
                output.append(f"   Draft Message Available: Yes")

            output.append("")

    return "\n".join(output)
```

### Structured JSON Output

```python
def format_recommendation_json(recommendations: list) -> dict:
    """
    Format recommendations for programmatic consumption
    """

    return {
        "generated_at": datetime.now().isoformat(),
        "total_recommendations": len(recommendations),
        "summary": {
            "critical": len([r for r in recommendations if r["priority"] == "critical"]),
            "high": len([r for r in recommendations if r["priority"] == "high"]),
            "medium": len([r for r in recommendations if r["priority"] == "medium"])
        },
        "recommendations": [
            {
                "id": rec["id"],
                "priority": rec["priority"],
                "category": rec["category"],
                "action": rec["action"],
                "rationale": rec["rationale"],
                "confidence": rec["confidence_score"],
                "score": rec["score"],
                "urgency": rec["urgency"],
                "estimated_effort": rec["estimated_effort"],
                "expected_impact": rec.get("expected_impact"),
                "expected_value": rec.get("expected_value"),
                "success_criteria": rec.get("success_criteria"),
                "next_steps": rec.get("next_steps", []),
                "draft_message": rec.get("draft_message"),
                "talking_points": rec.get("talking_points", [])
            }
            for rec in recommendations
        ]
    }
```

## Integration with Agent Workflows

### Recommendation Author Subagent

```python
recommendation_author_config = {
    "name": "Recommendation Author",
    "system_prompt": """
    You are a Recommendation Author specialized in generating actionable guidance for account executives.

    Your role:
    1. Analyze account health, risks, and opportunities
    2. Generate specific, actionable recommendations
    3. Draft communication templates when appropriate
    4. Prioritize actions by impact and urgency
    5. Provide clear rationale and success criteria

    Principles:
    - Every recommendation must be actionable
    - Include specific next steps and timelines
    - Provide talking points for customer conversations
    - Consider account owner workload and preferences
    - Base recommendations on data, not assumptions
    - Always include confidence scores and rationale

    Output Format:
    - Priority level (critical/high/medium/low)
    - Specific action to take
    - Clear rationale with supporting data
    - Estimated effort and timeline
    - Expected outcome or value
    - Success criteria
    - Draft communication if applicable
    """,
    "allowed_tools": [
        "Write",
        "Read",
        "search_account_history",
        "get_account_timeline"
    ],
    "permission_mode": "default"
}
```

### Human-in-the-Loop Approval

```python
async def recommendation_approval_workflow(
    recommendations: list,
    account_owner_email: str
) -> list:
    """
    Present recommendations for human approval

    Workflow:
    1. Format recommendations for review
    2. Present to account owner
    3. Capture feedback (approve/modify/reject)
    4. Execute approved actions
    5. Log decisions and outcomes
    """

    approved_recommendations = []

    for rec in recommendations:
        print(f"\n{'='*60}")
        print(f"Recommendation: {rec['action']}")
        print(f"Priority: {rec['priority']}")
        print(f"Rationale: {rec['rationale']}")
        print(f"Effort: {rec['estimated_effort']}")

        if rec.get("draft_message"):
            print(f"\nDraft Message:\n{rec['draft_message']}")

        decision = input("\nDecision (approve/modify/reject/skip): ").lower()

        if decision == "approve":
            approved_recommendations.append(rec)
            print("✓ Approved")

        elif decision == "modify":
            modifications = input("Enter modifications: ")
            rec["modifications"] = modifications
            rec["modified_by_human"] = True
            approved_recommendations.append(rec)
            print("✓ Approved with modifications")

        elif decision == "reject":
            reject_reason = input("Reason for rejection: ")
            rec["rejected"] = True
            rec["rejection_reason"] = reject_reason
            print("✗ Rejected")

        else:
            print("⊘ Skipped")

    return approved_recommendations
```

## Best Practices

1. **Actionability First**
   - Every recommendation must have a clear, specific action
   - Include next steps, timelines, and success criteria
   - Provide tools/templates to execute (draft emails, scripts)

2. **Context-Aware**
   - Consider account history and patterns
   - Respect customer communication preferences
   - Account for owner workload and capacity

3. **Confidence Transparency**
   - Always include confidence scores
   - Explain rationale with supporting data
   - Flag assumptions and uncertainties

4. **Human-Centric**
   - Recommendations augment, not replace, human judgment
   - Require approval for high-stakes actions
   - Learn from acceptance/rejection patterns

5. **Continuous Improvement**
   - Track recommendation outcomes
   - Measure acceptance rates by type
   - Refine scoring models based on results

## Resources

See `references/api_reference.md` for:
- Complete template library
- Scoring algorithm details
- Integration examples
- Best practices guide

See `scripts/` for:
- Recommendation generation utilities
- Template customization tools
- Approval workflow implementations
