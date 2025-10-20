"""
Historical interaction data fixtures for E2E testing.

Provides realistic:
- Email interactions
- Call logs
- Meeting notes
- Support tickets
- Product usage data
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import random


class InteractionFixtureGenerator:
    """Generate realistic interaction history."""

    INTERACTION_TYPES = [
        "Call", "Email", "Meeting", "Support_Ticket",
        "Demo", "Training", "QBR", "Product_Usage"
    ]

    EMAIL_SUBJECTS = [
        "Quarterly Business Review",
        "Product Update Discussion",
        "Contract Renewal",
        "Feature Request Follow-up",
        "Technical Support Issue",
        "Account Health Check",
        "Expansion Opportunity",
        "Training Session Scheduled",
        "Executive Briefing",
        "Partnership Discussion"
    ]

    CALL_SUBJECTS = [
        "Weekly Sync Call",
        "Product Demo",
        "Issue Resolution",
        "Strategic Planning",
        "Renewal Discussion",
        "Feature Walkthrough",
        "Support Escalation",
        "Account Review"
    ]

    MEETING_SUBJECTS = [
        "Quarterly Business Review",
        "Executive Roundtable",
        "Product Roadmap Discussion",
        "Contract Negotiation",
        "Implementation Planning",
        "Success Planning Session",
        "Training Workshop",
        "Technical Deep Dive"
    ]

    @classmethod
    def generate_email_interactions(
        cls,
        account_id: str,
        count: int = 10,
        days_back: int = 90
    ) -> List[Dict[str, Any]]:
        """Generate email interaction history."""
        interactions = []
        base_date = datetime.now()

        for i in range(count):
            interaction_date = base_date - timedelta(days=random.randint(1, days_back))
            interactions.append({
                "id": f"email_{account_id}_{i}",
                "account_id": account_id,
                "type": "Email",
                "subject": random.choice(cls.EMAIL_SUBJECTS),
                "date": interaction_date.isoformat(),
                "status": "Completed",
                "direction": random.choice(["Inbound", "Outbound"]),
                "sentiment": random.choice(["Positive", "Neutral", "Negative"]),
                "contact_name": f"Contact {random.randint(1, 5)}",
                "duration_minutes": None,
                "description": f"Email interaction regarding {random.choice(cls.EMAIL_SUBJECTS).lower()}",
                "created_at": interaction_date.isoformat(),
            })

        return sorted(interactions, key=lambda x: x["date"], reverse=True)

    @classmethod
    def generate_call_interactions(
        cls,
        account_id: str,
        count: int = 8,
        days_back: int = 90
    ) -> List[Dict[str, Any]]:
        """Generate call interaction history."""
        interactions = []
        base_date = datetime.now()

        for i in range(count):
            interaction_date = base_date - timedelta(days=random.randint(1, days_back))
            interactions.append({
                "id": f"call_{account_id}_{i}",
                "account_id": account_id,
                "type": "Call",
                "subject": random.choice(cls.CALL_SUBJECTS),
                "date": interaction_date.isoformat(),
                "status": "Completed",
                "direction": random.choice(["Inbound", "Outbound"]),
                "duration_minutes": random.randint(15, 60),
                "sentiment": random.choice(["Positive", "Neutral", "Negative"]),
                "contact_name": f"Contact {random.randint(1, 5)}",
                "call_outcome": random.choice([
                    "Next Steps Defined",
                    "Follow-up Required",
                    "Issue Resolved",
                    "Demo Scheduled"
                ]),
                "description": f"Call discussion about {random.choice(cls.CALL_SUBJECTS).lower()}",
                "created_at": interaction_date.isoformat(),
            })

        return sorted(interactions, key=lambda x: x["date"], reverse=True)

    @classmethod
    def generate_meeting_interactions(
        cls,
        account_id: str,
        count: int = 5,
        days_back: int = 180
    ) -> List[Dict[str, Any]]:
        """Generate meeting interaction history."""
        interactions = []
        base_date = datetime.now()

        for i in range(count):
            interaction_date = base_date - timedelta(days=random.randint(1, days_back))
            interactions.append({
                "id": f"meeting_{account_id}_{i}",
                "account_id": account_id,
                "type": "Meeting",
                "subject": random.choice(cls.MEETING_SUBJECTS),
                "date": interaction_date.isoformat(),
                "status": random.choice(["Completed", "Scheduled"]),
                "duration_minutes": random.randint(30, 120),
                "attendees": random.randint(2, 8),
                "sentiment": random.choice(["Positive", "Neutral"]),
                "meeting_type": random.choice(["In-Person", "Virtual", "Hybrid"]),
                "action_items_count": random.randint(0, 5),
                "description": f"Meeting for {random.choice(cls.MEETING_SUBJECTS).lower()}",
                "created_at": interaction_date.isoformat(),
            })

        return sorted(interactions, key=lambda x: x["date"], reverse=True)

    @classmethod
    def generate_support_tickets(
        cls,
        account_id: str,
        count: int = 5,
        days_back: int = 180
    ) -> List[Dict[str, Any]]:
        """Generate support ticket history."""
        tickets = []
        base_date = datetime.now()

        for i in range(count):
            created_date = base_date - timedelta(days=random.randint(1, days_back))
            status = random.choice(["Open", "In Progress", "Resolved", "Closed"])

            resolved_date = None
            if status in ["Resolved", "Closed"]:
                resolved_date = (created_date + timedelta(days=random.randint(1, 14))).isoformat()

            tickets.append({
                "id": f"ticket_{account_id}_{i}",
                "account_id": account_id,
                "type": "Support_Ticket",
                "subject": f"Support Issue #{1000 + i}",
                "priority": random.choice(["Low", "Medium", "High", "Critical"]),
                "status": status,
                "category": random.choice([
                    "Technical Issue",
                    "Feature Request",
                    "Bug Report",
                    "Configuration Help",
                    "Training Request",
                    "Account Question"
                ]),
                "created_date": created_date.isoformat(),
                "resolved_date": resolved_date,
                "resolution_time_hours": random.randint(1, 336) if resolved_date else None,
                "satisfaction_score": random.randint(1, 5) if resolved_date else None,
                "description": f"Customer support ticket for technical assistance",
            })

        return sorted(tickets, key=lambda x: x["created_date"], reverse=True)

    @classmethod
    def generate_product_usage(
        cls,
        account_id: str,
        days_back: int = 90
    ) -> List[Dict[str, Any]]:
        """Generate product usage data."""
        usage_data = []
        base_date = datetime.now()

        # Generate daily usage for the past N days
        for day in range(days_back):
            usage_date = base_date - timedelta(days=day)

            # Simulate varying usage patterns
            usage_level = random.choice(["high", "medium", "low", "none"])

            if usage_level == "high":
                logins = random.randint(20, 100)
                feature_usage = random.randint(50, 200)
            elif usage_level == "medium":
                logins = random.randint(5, 20)
                feature_usage = random.randint(10, 50)
            elif usage_level == "low":
                logins = random.randint(1, 5)
                feature_usage = random.randint(1, 10)
            else:  # none
                logins = 0
                feature_usage = 0

            usage_data.append({
                "id": f"usage_{account_id}_{day}",
                "account_id": account_id,
                "type": "Product_Usage",
                "date": usage_date.date().isoformat(),
                "total_logins": logins,
                "unique_users": min(logins, random.randint(1, 10)),
                "feature_usage_count": feature_usage,
                "session_duration_minutes": random.randint(10, 240) if logins > 0 else 0,
                "api_calls": random.randint(100, 10000) if logins > 0 else 0,
                "errors_count": random.randint(0, 5),
                "created_at": usage_date.isoformat(),
            })

        return usage_data


def generate_complete_interaction_history(
    account_id: str,
    account_type: str = "healthy"
) -> List[Dict[str, Any]]:
    """Generate complete interaction history for an account.

    Args:
        account_id: Account identifier
        account_type: Type of account (healthy, at_risk, high_value, growth)

    Returns:
        Combined list of all interactions
    """
    all_interactions = []

    if account_type == "healthy":
        all_interactions.extend(InteractionFixtureGenerator.generate_email_interactions(account_id, 10, 90))
        all_interactions.extend(InteractionFixtureGenerator.generate_call_interactions(account_id, 8, 90))
        all_interactions.extend(InteractionFixtureGenerator.generate_meeting_interactions(account_id, 5, 180))
        all_interactions.extend(InteractionFixtureGenerator.generate_support_tickets(account_id, 2, 180))
        all_interactions.extend(InteractionFixtureGenerator.generate_product_usage(account_id, 90))

    elif account_type == "at_risk":
        all_interactions.extend(InteractionFixtureGenerator.generate_email_interactions(account_id, 3, 180))
        all_interactions.extend(InteractionFixtureGenerator.generate_call_interactions(account_id, 2, 180))
        all_interactions.extend(InteractionFixtureGenerator.generate_meeting_interactions(account_id, 1, 365))
        all_interactions.extend(InteractionFixtureGenerator.generate_support_tickets(account_id, 8, 180))
        all_interactions.extend(InteractionFixtureGenerator.generate_product_usage(account_id, 90))

    elif account_type == "high_value":
        all_interactions.extend(InteractionFixtureGenerator.generate_email_interactions(account_id, 20, 90))
        all_interactions.extend(InteractionFixtureGenerator.generate_call_interactions(account_id, 15, 90))
        all_interactions.extend(InteractionFixtureGenerator.generate_meeting_interactions(account_id, 8, 180))
        all_interactions.extend(InteractionFixtureGenerator.generate_support_tickets(account_id, 1, 180))
        all_interactions.extend(InteractionFixtureGenerator.generate_product_usage(account_id, 90))

    elif account_type == "growth":
        all_interactions.extend(InteractionFixtureGenerator.generate_email_interactions(account_id, 12, 90))
        all_interactions.extend(InteractionFixtureGenerator.generate_call_interactions(account_id, 10, 90))
        all_interactions.extend(InteractionFixtureGenerator.generate_meeting_interactions(account_id, 6, 180))
        all_interactions.extend(InteractionFixtureGenerator.generate_support_tickets(account_id, 3, 180))
        all_interactions.extend(InteractionFixtureGenerator.generate_product_usage(account_id, 90))

    return all_interactions
