"""
Deal pipeline data fixtures for E2E testing.

Provides realistic:
- Deal stages and progression
- Revenue forecasting
- Win/loss tracking
- Deal timeline data
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import random


class DealFixtureGenerator:
    """Generate realistic deal pipeline data."""

    DEAL_STAGES = [
        "Qualification",
        "Needs Analysis",
        "Proposal",
        "Negotiation",
        "Closed Won",
        "Closed Lost"
    ]

    DEAL_TYPES = [
        "New Business",
        "Upsell",
        "Renewal",
        "Cross-sell",
        "Expansion"
    ]

    LOSS_REASONS = [
        "Competitor",
        "Price",
        "No Budget",
        "Timing",
        "No Decision",
        "Product Fit"
    ]

    @classmethod
    def generate_active_deals(
        cls,
        account_id: str,
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate active pipeline deals."""
        deals = []
        base_date = datetime.now()

        for i in range(count):
            created_date = base_date - timedelta(days=random.randint(30, 180))
            close_date = base_date + timedelta(days=random.randint(30, 120))

            stage = random.choice(cls.DEAL_STAGES[:-2])  # Exclude closed stages
            probability = {
                "Qualification": random.randint(10, 25),
                "Needs Analysis": random.randint(25, 40),
                "Proposal": random.randint(40, 60),
                "Negotiation": random.randint(60, 90)
            }[stage]

            deal_value = random.randint(50000, 1000000)

            deals.append({
                "id": f"deal_{account_id}_{i}",
                "account_id": account_id,
                "Deal_Name": f"{random.choice(cls.DEAL_TYPES)} - Deal {i+1}",
                "Amount": deal_value,
                "Stage": stage,
                "Probability": probability,
                "Expected_Revenue": int(deal_value * probability / 100),
                "Closing_Date": close_date.date().isoformat(),
                "Deal_Type": random.choice(cls.DEAL_TYPES),
                "Lead_Source": random.choice(["Inbound", "Outbound", "Referral", "Partner"]),
                "Next_Step": cls._get_next_step(stage),
                "Days_in_Stage": random.randint(1, 45),
                "Created_Time": created_date.isoformat(),
                "Modified_Time": (base_date - timedelta(days=random.randint(1, 7))).isoformat(),
                "Owner": {
                    "id": f"sales_rep_{random.randint(1, 5)}",
                    "name": f"Sales Rep {random.randint(1, 5)}"
                },
                "Products": cls._generate_deal_products(),
                "Competitors": random.sample(
                    ["Competitor A", "Competitor B", "Competitor C"],
                    random.randint(0, 2)
                ) if random.random() > 0.5 else []
            })

        return deals

    @classmethod
    def generate_closed_won_deals(
        cls,
        account_id: str,
        count: int = 5,
        days_back: int = 365
    ) -> List[Dict[str, Any]]:
        """Generate historical won deals."""
        deals = []
        base_date = datetime.now()

        for i in range(count):
            created_date = base_date - timedelta(days=random.randint(days_back + 90, days_back + 365))
            close_date = base_date - timedelta(days=random.randint(1, days_back))

            deal_value = random.randint(100000, 2000000)

            deals.append({
                "id": f"deal_won_{account_id}_{i}",
                "account_id": account_id,
                "Deal_Name": f"{random.choice(cls.DEAL_TYPES)} - Historical {i+1}",
                "Amount": deal_value,
                "Stage": "Closed Won",
                "Probability": 100,
                "Expected_Revenue": deal_value,
                "Closing_Date": close_date.date().isoformat(),
                "Deal_Type": random.choice(cls.DEAL_TYPES),
                "Lead_Source": random.choice(["Inbound", "Outbound", "Referral", "Partner"]),
                "Created_Time": created_date.isoformat(),
                "Modified_Time": close_date.isoformat(),
                "Closed_Time": close_date.isoformat(),
                "Owner": {
                    "id": f"sales_rep_{random.randint(1, 5)}",
                    "name": f"Sales Rep {random.randint(1, 5)}"
                },
                "Products": cls._generate_deal_products(),
                "Sales_Cycle_Days": (close_date - created_date).days,
                "Discount_Percentage": random.randint(0, 20) if random.random() > 0.5 else 0
            })

        return deals

    @classmethod
    def generate_closed_lost_deals(
        cls,
        account_id: str,
        count: int = 2,
        days_back: int = 365
    ) -> List[Dict[str, Any]]:
        """Generate historical lost deals."""
        deals = []
        base_date = datetime.now()

        for i in range(count):
            created_date = base_date - timedelta(days=random.randint(days_back + 90, days_back + 365))
            close_date = base_date - timedelta(days=random.randint(1, days_back))

            deal_value = random.randint(50000, 1000000)
            loss_reason = random.choice(cls.LOSS_REASONS)

            deals.append({
                "id": f"deal_lost_{account_id}_{i}",
                "account_id": account_id,
                "Deal_Name": f"{random.choice(cls.DEAL_TYPES)} - Lost {i+1}",
                "Amount": deal_value,
                "Stage": "Closed Lost",
                "Probability": 0,
                "Expected_Revenue": 0,
                "Closing_Date": close_date.date().isoformat(),
                "Deal_Type": random.choice(cls.DEAL_TYPES),
                "Lead_Source": random.choice(["Inbound", "Outbound", "Referral", "Partner"]),
                "Loss_Reason": loss_reason,
                "Created_Time": created_date.isoformat(),
                "Modified_Time": close_date.isoformat(),
                "Closed_Time": close_date.isoformat(),
                "Owner": {
                    "id": f"sales_rep_{random.randint(1, 5)}",
                    "name": f"Sales Rep {random.randint(1, 5)}"
                },
                "Products": cls._generate_deal_products(),
                "Sales_Cycle_Days": (close_date - created_date).days,
                "Competitor_Won": random.choice(["Competitor A", "Competitor B", "Competitor C"])
                    if loss_reason == "Competitor" else None
            })

        return deals

    @staticmethod
    def _get_next_step(stage: str) -> str:
        """Get appropriate next step for stage."""
        next_steps = {
            "Qualification": "Schedule discovery call",
            "Needs Analysis": "Prepare proposal",
            "Proposal": "Schedule proposal review",
            "Negotiation": "Finalize contract terms"
        }
        return next_steps.get(stage, "Follow up")

    @staticmethod
    def _generate_deal_products() -> List[Dict[str, Any]]:
        """Generate products in a deal."""
        products = [
            {"name": "Enterprise License", "quantity": random.randint(10, 100)},
            {"name": "Professional Services", "quantity": random.randint(20, 200)},
            {"name": "Training Package", "quantity": random.randint(5, 50)},
            {"name": "Support Contract", "quantity": random.randint(1, 10)}
        ]
        return random.sample(products, random.randint(1, 3))


def generate_complete_deal_pipeline(
    account_id: str,
    account_type: str = "healthy"
) -> Dict[str, List[Dict[str, Any]]]:
    """Generate complete deal pipeline for an account.

    Args:
        account_id: Account identifier
        account_type: Type of account (healthy, at_risk, high_value, growth)

    Returns:
        Dictionary with active, won, and lost deals
    """
    if account_type == "healthy":
        active_count = random.randint(2, 4)
        won_count = random.randint(3, 6)
        lost_count = random.randint(1, 2)
    elif account_type == "at_risk":
        active_count = 0
        won_count = random.randint(1, 3)
        lost_count = random.randint(2, 4)
    elif account_type == "high_value":
        active_count = random.randint(5, 10)
        won_count = random.randint(8, 15)
        lost_count = random.randint(0, 2)
    elif account_type == "growth":
        active_count = random.randint(2, 5)
        won_count = random.randint(2, 5)
        lost_count = random.randint(1, 3)
    else:
        active_count = 2
        won_count = 3
        lost_count = 1

    return {
        "active": DealFixtureGenerator.generate_active_deals(account_id, active_count),
        "won": DealFixtureGenerator.generate_closed_won_deals(account_id, won_count),
        "lost": DealFixtureGenerator.generate_closed_lost_deals(account_id, lost_count)
    }


def calculate_pipeline_metrics(deals: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Calculate pipeline metrics from deals.

    Args:
        deals: Dictionary containing active, won, and lost deals

    Returns:
        Pipeline metrics
    """
    active = deals.get("active", [])
    won = deals.get("won", [])
    lost = deals.get("lost", [])

    total_pipeline_value = sum(d["Amount"] for d in active)
    weighted_pipeline = sum(d["Expected_Revenue"] for d in active)
    total_won_value = sum(d["Amount"] for d in won)
    total_lost_value = sum(d["Amount"] for d in lost)

    total_closed = len(won) + len(lost)
    win_rate = (len(won) / total_closed * 100) if total_closed > 0 else 0

    avg_deal_size = (total_won_value / len(won)) if won else 0
    avg_sales_cycle = (sum(d.get("Sales_Cycle_Days", 0) for d in won) / len(won)) if won else 0

    return {
        "total_active_deals": len(active),
        "total_pipeline_value": total_pipeline_value,
        "weighted_pipeline_value": weighted_pipeline,
        "total_won_deals": len(won),
        "total_won_value": total_won_value,
        "total_lost_deals": len(lost),
        "total_lost_value": total_lost_value,
        "win_rate_percentage": round(win_rate, 2),
        "average_deal_size": round(avg_deal_size, 2),
        "average_sales_cycle_days": round(avg_sales_cycle, 2)
    }
