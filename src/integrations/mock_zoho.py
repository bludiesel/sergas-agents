"""
Mock Zoho Integration for Testing
Simulates Zoho CRM responses without requiring credentials
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
from uuid import uuid4


class MockZohoIntegration:
    """Mock Zoho CRM client for testing without credentials"""

    def __init__(self):
        self.mock_accounts = self._generate_mock_accounts()

    def _generate_mock_accounts(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate realistic mock account data"""
        accounts = []
        statuses = ["Active", "Inactive", "At Risk", "Churned"]
        industries = ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing"]

        for i in range(count):
            account_id = f"ACC{1000 + i}"
            accounts.append({
                "id": account_id,
                "Account_Name": f"Test Company {i+1}",
                "Account_Owner": {
                    "id": f"OWNER{(i % 3) + 1}",
                    "name": f"Account Executive {(i % 3) + 1}"
                },
                "Account_Status": random.choice(statuses),
                "Industry": random.choice(industries),
                "Annual_Revenue": random.randint(100000, 10000000),
                "Number_of_Employees": random.randint(10, 5000),
                "Created_Time": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                "Modified_Time": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "Last_Activity_Time": (datetime.now() - timedelta(days=random.randint(0, 60))).isoformat(),
                "Description": f"Mock account for testing - {account_id}",
                "Phone": f"+1-555-{random.randint(1000, 9999)}",
                "Website": f"https://testcompany{i+1}.example.com"
            })

        return accounts

    async def get_accounts_by_owner(
        self,
        owner_id: str,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """Mock: Get accounts by owner"""
        filtered = [acc for acc in self.mock_accounts if acc["Account_Owner"]["id"] == owner_id]

        return {
            "data": filtered,
            "info": {
                "count": len(filtered),
                "page": page,
                "per_page": per_page,
                "more_records": False
            }
        }

    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Mock: Get single account"""
        for acc in self.mock_accounts:
            if acc["id"] == account_id:
                return {"data": [acc]}
        return None

    async def get_account_deals(self, account_id: str) -> Dict[str, Any]:
        """Mock: Get deals for account"""
        deal_stages = ["Prospecting", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
        num_deals = random.randint(0, 5)

        deals = []
        for i in range(num_deals):
            deals.append({
                "id": f"DEAL{uuid4().hex[:8]}",
                "Deal_Name": f"Deal {i+1} for {account_id}",
                "Account_Name": {"id": account_id},
                "Amount": random.randint(10000, 500000),
                "Stage": random.choice(deal_stages),
                "Closing_Date": (datetime.now() + timedelta(days=random.randint(0, 90))).isoformat(),
                "Probability": random.randint(0, 100),
                "Created_Time": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
            })

        return {"data": deals}

    async def get_account_activities(
        self,
        account_id: str,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Mock: Get activities for account"""
        activity_types = ["Call", "Meeting", "Email", "Task"]
        num_activities = random.randint(2, 10)

        activities = []
        for i in range(num_activities):
            activity_time = datetime.now() - timedelta(days=random.randint(0, 30))

            if since and activity_time < since:
                continue

            activities.append({
                "id": f"ACT{uuid4().hex[:8]}",
                "Activity_Type": random.choice(activity_types),
                "Subject": f"Mock {random.choice(activity_types)}: Follow-up",
                "Related_To": {"id": account_id},
                "Status": random.choice(["Completed", "Scheduled", "Cancelled"]),
                "Due_Date": activity_time.isoformat(),
                "Created_Time": (activity_time - timedelta(hours=1)).isoformat()
            })

        return {"data": activities}

    async def get_account_notes(self, account_id: str) -> Dict[str, Any]:
        """Mock: Get notes for account"""
        num_notes = random.randint(0, 5)

        notes = []
        for i in range(num_notes):
            notes.append({
                "id": f"NOTE{uuid4().hex[:8]}",
                "Note_Title": f"Mock Note {i+1}",
                "Note_Content": f"This is a test note for account {account_id}. Meeting went well, customer interested in expanding.",
                "Parent_Id": {"id": account_id},
                "Created_Time": (datetime.now() - timedelta(days=random.randint(0, 60))).isoformat(),
                "Modified_Time": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
            })

        return {"data": notes}

    async def detect_changes(
        self,
        account_id: str,
        last_sync: datetime
    ) -> Dict[str, Any]:
        """Mock: Detect changes since last sync"""
        account = await self.get_account(account_id)

        if not account or not account.get("data"):
            return {"has_changes": False, "changes": []}

        account_data = account["data"][0]
        modified_time = datetime.fromisoformat(account_data["Modified_Time"].replace("Z", ""))

        has_changes = modified_time > last_sync

        changes = []
        if has_changes:
            # Simulate field changes
            changed_fields = random.sample(
                ["Account_Status", "Annual_Revenue", "Number_of_Employees", "Description"],
                k=random.randint(1, 3)
            )

            for field in changed_fields:
                changes.append({
                    "field": field,
                    "old_value": "Previous Value",
                    "new_value": account_data.get(field),
                    "changed_at": account_data["Modified_Time"]
                })

        return {
            "has_changes": has_changes,
            "changes": changes,
            "last_modified": account_data["Modified_Time"]
        }

    async def search_accounts(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Mock: Search accounts"""
        # Simple mock search - return all accounts
        return {
            "data": self.mock_accounts[:5],  # Limit to 5 for testing
            "info": {
                "count": 5,
                "more_records": False
            }
        }


class MockCogneeIntegration:
    """Mock Cognee memory client for testing"""

    def __init__(self):
        self.memory_store: Dict[str, Any] = {}

    async def store_memory(
        self,
        account_id: str,
        memory_type: str,
        data: Dict[str, Any]
    ):
        """Mock: Store memory"""
        key = f"{account_id}:{memory_type}"
        self.memory_store[key] = {
            "data": data,
            "stored_at": datetime.now().isoformat()
        }

    async def get_historical_context(
        self,
        account_id: str
    ) -> Dict[str, Any]:
        """Mock: Get historical context"""
        return {
            "account_id": account_id,
            "summary": f"Historical context for {account_id}",
            "key_events": [
                {
                    "event": "Account Created",
                    "date": (datetime.now() - timedelta(days=180)).isoformat(),
                    "description": "Account initially created"
                },
                {
                    "event": "First Deal Won",
                    "date": (datetime.now() - timedelta(days=120)).isoformat(),
                    "description": "First successful deal closed"
                },
                {
                    "event": "Expansion Discussion",
                    "date": (datetime.now() - timedelta(days=30)).isoformat(),
                    "description": "Customer showed interest in expanding services"
                }
            ],
            "sentiment_trend": "positive",
            "relationship_strength": "strong",
            "commitment_tracking": [
                {
                    "commitment": "Implement new feature",
                    "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                    "status": "in_progress"
                }
            ]
        }

    async def identify_patterns(
        self,
        account_id: str
    ) -> List[Dict[str, Any]]:
        """Mock: Identify patterns"""
        patterns = [
            {
                "pattern_type": "engagement_increase",
                "description": "Engagement has increased 30% over last quarter",
                "confidence": 0.85,
                "detected_at": datetime.now().isoformat()
            },
            {
                "pattern_type": "expansion_signal",
                "description": "Multiple inquiries about additional products",
                "confidence": 0.72,
                "detected_at": datetime.now().isoformat()
            }
        ]

        return patterns

    async def query_memory(
        self,
        account_id: str,
        query: str
    ) -> Dict[str, Any]:
        """Mock: Query memory"""
        return {
            "query": query,
            "results": [
                {
                    "content": f"Mock memory result for {account_id}",
                    "relevance": 0.9,
                    "source": "historical_notes"
                }
            ]
        }


# Singleton instances
_mock_zoho: Optional[MockZohoIntegration] = None
_mock_cognee: Optional[MockCogneeIntegration] = None


def get_mock_zoho() -> MockZohoIntegration:
    """Get singleton mock Zoho client"""
    global _mock_zoho
    if _mock_zoho is None:
        _mock_zoho = MockZohoIntegration()
    return _mock_zoho


def get_mock_cognee() -> MockCogneeIntegration:
    """Get singleton mock Cognee client"""
    global _mock_cognee
    if _mock_cognee is None:
        _mock_cognee = MockCogneeIntegration()
    return _mock_cognee
