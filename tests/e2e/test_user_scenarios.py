"""
End-to-End User Scenario Tests.

Tests cover realistic user workflows:
- Daily review scenario
- Weekly review scenario
- On-demand review scenario
- Escalation scenario
- Approval/rejection scenario
- Multi-user collaboration
- Performance under realistic load

Uses real database with mocked external APIs.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, Mock

from tests.e2e.fixtures.account_fixtures import (
    get_all_test_accounts,
    get_accounts_by_owner,
    get_high_risk_accounts
)
from tests.e2e.fixtures.interaction_fixtures import generate_complete_interaction_history
from tests.e2e.fixtures.deal_fixtures import (
    generate_complete_deal_pipeline,
    calculate_pipeline_metrics
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_notification_service():
    """Mock notification service for user alerts."""
    service = AsyncMock()
    sent_notifications = []

    async def send_email(to: str, subject: str, body: str):
        notification = {
            "type": "email",
            "to": to,
            "subject": subject,
            "body": body,
            "sent_at": datetime.now()
        }
        sent_notifications.append(notification)
        return {"success": True, "notification_id": f"notif_{len(sent_notifications)}"}

    async def send_slack(channel: str, message: str):
        notification = {
            "type": "slack",
            "channel": channel,
            "message": message,
            "sent_at": datetime.now()
        }
        sent_notifications.append(notification)
        return {"success": True, "notification_id": f"notif_{len(sent_notifications)}"}

    service.send_email = send_email
    service.send_slack = send_slack
    service.sent_notifications = sent_notifications

    return service


@pytest.fixture
def mock_reporting_service():
    """Mock reporting service for generating user reports."""
    service = AsyncMock()
    generated_reports = []

    async def generate_owner_brief(owner_id: str, cycle: str, accounts: List[Dict]):
        brief = {
            "owner_id": owner_id,
            "cycle": cycle,
            "generated_at": datetime.now(),
            "accounts_reviewed": len(accounts),
            "summary": {
                "total_accounts": len(accounts),
                "high_priority": len([a for a in accounts if a.get("priority") == "high"]),
                "action_required": len([a for a in accounts if a.get("requires_action")])
            },
            "accounts": accounts
        }
        generated_reports.append(brief)
        return brief

    async def generate_executive_summary(accounts: List[Dict]):
        summary = {
            "generated_at": datetime.now(),
            "total_accounts": len(accounts),
            "health_distribution": {
                "healthy": len([a for a in accounts if a.get("health_score", 0) >= 70]),
                "at_risk": len([a for a in accounts if 40 <= a.get("health_score", 0) < 70]),
                "critical": len([a for a in accounts if a.get("health_score", 0) < 40])
            },
            "total_revenue": sum(a.get("Annual_Revenue", 0) for a in accounts)
        }
        generated_reports.append(summary)
        return summary

    service.generate_owner_brief = generate_owner_brief
    service.generate_executive_summary = generate_executive_summary
    service.generated_reports = generated_reports

    return service


# ============================================================================
# Test Suite: Daily Review Scenario
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestDailyReviewScenario:
    """Test complete daily review workflow from user perspective."""

    async def test_account_manager_daily_review(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e,
        mock_claude_agent,
        mock_reporting_service,
        mock_notification_service
    ):
        """
        Scenario: Account Manager receives and reviews daily brief.

        User Story: As an account manager, I want to receive a daily brief
        of my accounts so I can prioritize my work for the day.
        """
        # Arrange
        owner_id = "owner_1"
        owner_email = "manager1@company.com"
        all_accounts = get_all_test_accounts()
        owner_accounts = get_accounts_by_owner(owner_id, all_accounts)

        # Act
        # 1. System generates daily brief (morning automation)
        account_analyses = []
        for account in owner_accounts[:10]:  # Sample 10 accounts
            # Fetch latest data
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            activities = await mock_zoho_client_e2e.get_activities(account["id"])

            # Analyze
            health_analysis = await mock_claude_agent.query(
                f"Daily health check for {account['id']}",
                {"account": account_data, "activities": activities}
            )

            account_analyses.append({
                "account_id": account["id"],
                "account_name": account.get("Account_Name"),
                "health_score": health_analysis.get("health_score", 75),
                "priority": "high" if health_analysis.get("health_score", 75) < 60 else "medium",
                "requires_action": health_analysis.get("health_score", 75) < 60,
                "key_insights": health_analysis.get("key_findings", [])
            })

        # 2. Generate and send daily brief
        brief = await mock_reporting_service.generate_owner_brief(
            owner_id, "daily", account_analyses
        )

        await mock_notification_service.send_email(
            to=owner_email,
            subject=f"Daily Account Brief - {datetime.now().strftime('%Y-%m-%d')}",
            body=f"You have {brief['summary']['action_required']} accounts requiring attention."
        )

        # 3. User reviews brief (simulated)
        high_priority_accounts = [a for a in account_analyses if a["priority"] == "high"]

        # Assert
        assert brief["accounts_reviewed"] == 10
        assert brief["summary"]["total_accounts"] == 10
        assert len(mock_notification_service.sent_notifications) == 1
        assert mock_notification_service.sent_notifications[0]["to"] == owner_email

        # Verify prioritization works
        if high_priority_accounts:
            assert all(a["health_score"] < 60 for a in high_priority_accounts)

    async def test_multi_manager_daily_briefing(
        self,
        mock_zoho_client_e2e,
        mock_claude_agent,
        mock_reporting_service,
        mock_notification_service
    ):
        """
        Scenario: Multiple account managers receive their daily briefs.

        User Story: As a sales director, I want all my account managers
        to receive their daily briefs simultaneously each morning.
        """
        # Arrange
        managers = [
            {"id": "owner_1", "email": "manager1@company.com"},
            {"id": "owner_2", "email": "manager2@company.com"},
            {"id": "owner_3", "email": "manager3@company.com"}
        ]
        all_accounts = get_all_test_accounts()

        # Act
        async def generate_manager_brief(manager):
            owner_accounts = get_accounts_by_owner(manager["id"], all_accounts)

            # Quick analysis for all accounts
            analyses = []
            for account in owner_accounts[:5]:
                account_data = await mock_zoho_client_e2e.get_account(account["id"])
                health = await mock_claude_agent.query(
                    f"Quick check {account['id']}", {"account": account_data}
                )
                analyses.append({
                    "account_id": account["id"],
                    "health_score": health.get("health_score", 75)
                })

            # Generate brief
            brief = await mock_reporting_service.generate_owner_brief(
                manager["id"], "daily", analyses
            )

            # Send notification
            await mock_notification_service.send_email(
                to=manager["email"],
                subject=f"Daily Brief - {datetime.now().strftime('%Y-%m-%d')}",
                body=f"Your daily account review is ready."
            )

            return brief

        # Generate all briefs in parallel
        briefs = await asyncio.gather(*[
            generate_manager_brief(mgr) for mgr in managers
        ])

        # Assert
        assert len(briefs) == 3
        assert all(brief["accounts_reviewed"] > 0 for brief in briefs)
        assert len(mock_notification_service.sent_notifications) == 3
        # All notifications sent to different managers
        sent_to = [n["to"] for n in mock_notification_service.sent_notifications]
        assert len(set(sent_to)) == 3


# ============================================================================
# Test Suite: Weekly Review Scenario
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestWeeklyReviewScenario:
    """Test weekly strategic review workflow."""

    async def test_account_manager_weekly_review(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e,
        mock_claude_agent,
        mock_reporting_service,
        mock_notification_service
    ):
        """
        Scenario: Account Manager receives comprehensive weekly review.

        User Story: As an account manager, I want a comprehensive weekly
        review with trends and strategic recommendations.
        """
        # Arrange
        owner_id = "owner_1"
        owner_email = "manager1@company.com"
        all_accounts = get_all_test_accounts()
        owner_accounts = get_accounts_by_owner(owner_id, all_accounts)

        # Act
        # 1. Deep analysis for weekly review
        weekly_analyses = []
        for account in owner_accounts[:10]:
            # Comprehensive data gathering
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            contacts = await mock_zoho_client_e2e.get_contacts(account["id"])
            deals = await mock_zoho_client_e2e.get_deals(account["id"])
            activities = await mock_zoho_client_e2e.get_activities(account["id"])

            # Historical context
            account_type = "healthy" if "HEALTHY" in account["id"] else "at_risk"
            history = generate_complete_interaction_history(account["id"], account_type)

            # Store complete context
            await mock_cognee_client_e2e.store(
                f"weekly_context_{account['id']}",
                {
                    "account": account_data,
                    "contacts": contacts,
                    "deals": deals,
                    "activities": activities,
                    "history_summary": {
                        "total_interactions": len(history),
                        "recent_interactions": len([h for h in history if
                            datetime.fromisoformat(h.get("date", h.get("created_at")))
                            > datetime.now() - timedelta(days=7)])
                    }
                }
            )

            # Deep analysis
            strategic_analysis = await mock_claude_agent.query(
                f"Weekly strategic analysis for {account['id']}",
                {
                    "account": account_data,
                    "contacts": contacts,
                    "deals": deals,
                    "history": history[:30]  # Recent history
                }
            )

            weekly_analyses.append({
                "account_id": account["id"],
                "account_name": account.get("Account_Name"),
                "health_score": strategic_analysis.get("health_score", 75),
                "trends": strategic_analysis.get("key_findings", []),
                "strategic_recommendations": strategic_analysis.get("recommendations", []),
                "deal_pipeline_value": sum(d.get("Amount", 0) for d in deals),
                "engagement_level": "high" if len(activities) > 10 else "medium"
            })

        # 2. Generate comprehensive weekly brief
        brief = await mock_reporting_service.generate_owner_brief(
            owner_id, "weekly", weekly_analyses
        )

        # 3. Send detailed notification
        await mock_notification_service.send_email(
            to=owner_email,
            subject=f"Weekly Strategic Review - Week of {datetime.now().strftime('%Y-%m-%d')}",
            body=f"Your weekly review is ready with {len(weekly_analyses)} accounts analyzed."
        )

        # Assert
        assert brief["accounts_reviewed"] == 10
        assert all("strategic_recommendations" in a for a in weekly_analyses)
        assert all("trends" in a for a in weekly_analyses)
        assert len(mock_notification_service.sent_notifications) == 1

    async def test_executive_weekly_rollup(
        self,
        mock_zoho_client_e2e,
        mock_reporting_service,
        mock_notification_service
    ):
        """
        Scenario: Executive receives weekly rollup across all accounts.

        User Story: As an executive, I want a weekly summary of all accounts
        with key metrics and trends.
        """
        # Arrange
        all_accounts = get_all_test_accounts()
        executive_email = "executive@company.com"

        # Act
        # 1. Gather account summaries
        account_summaries = []
        for account in all_accounts:
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            deals = await mock_zoho_client_e2e.get_deals(account["id"])

            account_summaries.append({
                "id": account["id"],
                "name": account.get("Account_Name"),
                "revenue": account.get("Annual_Revenue", 0),
                "health_score": account.get("Engagement_Score", 75),
                "pipeline_value": sum(d.get("Amount", 0) for d in deals),
                "rating": account.get("Rating", "Warm")
            })

        # 2. Generate executive summary
        executive_summary = await mock_reporting_service.generate_executive_summary(
            account_summaries
        )

        # 3. Send to executive
        await mock_notification_service.send_email(
            to=executive_email,
            subject=f"Executive Weekly Summary - {datetime.now().strftime('%Y-%m-%d')}",
            body=f"Portfolio health: {executive_summary['health_distribution']}"
        )

        # Assert
        assert executive_summary["total_accounts"] == len(all_accounts)
        assert "health_distribution" in executive_summary
        assert executive_summary["total_revenue"] > 0
        assert len(mock_notification_service.sent_notifications) == 1


# ============================================================================
# Test Suite: On-Demand Review Scenario
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestOnDemandReviewScenario:
    """Test on-demand review triggered by users."""

    async def test_manager_requests_account_analysis(
        self,
        mock_zoho_client_e2e,
        mock_cognee_client_e2e,
        mock_claude_agent,
        mock_notification_service
    ):
        """
        Scenario: Manager requests immediate analysis of specific account.

        User Story: As an account manager, I want to request an immediate
        analysis before an important meeting.
        """
        # Arrange
        account = get_all_test_accounts()[0]
        manager_email = "manager1@company.com"

        # Act
        # 1. Manager triggers on-demand review
        start_time = datetime.now()

        # 2. Gather comprehensive data
        account_data = await mock_zoho_client_e2e.get_account(account["id"])
        contacts = await mock_zoho_client_e2e.get_contacts(account["id"])
        deals = await mock_zoho_client_e2e.get_deals(account["id"])
        activities = await mock_zoho_client_e2e.get_activities(account["id"])

        # 3. Generate comprehensive analysis
        comprehensive_analysis = await mock_claude_agent.query(
            f"Comprehensive analysis for meeting preparation - {account['id']}",
            {
                "account": account_data,
                "contacts": contacts,
                "deals": deals,
                "activities": activities,
                "purpose": "meeting_preparation"
            }
        )

        # 4. Store for quick access
        await mock_cognee_client_e2e.store(
            f"ondemand_analysis_{account['id']}_{datetime.now().timestamp()}",
            {
                "analysis": comprehensive_analysis,
                "generated_at": datetime.now().isoformat(),
                "requested_by": manager_email
            }
        )

        # 5. Notify manager
        await mock_notification_service.send_email(
            to=manager_email,
            subject=f"Analysis Ready: {account.get('Account_Name')}",
            body=f"Your requested analysis is complete."
        )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Assert
        # Should complete quickly for meeting prep
        assert processing_time < 30  # Under 30 seconds
        assert comprehensive_analysis is not None
        assert len(mock_notification_service.sent_notifications) == 1

    async def test_bulk_on_demand_analysis(
        self,
        mock_zoho_client_e2e,
        mock_claude_agent
    ):
        """
        Scenario: Manager requests analysis for multiple accounts at once.

        User Story: As an account manager, I want to analyze multiple
        accounts before a planning session.
        """
        # Arrange
        all_accounts = get_all_test_accounts()
        target_accounts = get_high_risk_accounts(all_accounts, risk_threshold=70)[:5]

        # Act
        start_time = datetime.now()

        async def analyze_account(account):
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            analysis = await mock_claude_agent.query(
                f"Risk analysis {account['id']}", {"account": account_data}
            )
            return {
                "account_id": account["id"],
                "account_name": account.get("Account_Name"),
                "analysis": analysis
            }

        # Parallel analysis
        analyses = await asyncio.gather(*[
            analyze_account(acc) for acc in target_accounts
        ])

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Assert
        assert len(analyses) == 5
        assert processing_time < 60  # Complete 5 accounts in under 1 minute
        assert all("analysis" in a for a in analyses)


# ============================================================================
# Test Suite: Escalation Scenario
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestEscalationScenario:
    """Test account escalation workflows."""

    async def test_critical_account_escalation(
        self,
        mock_zoho_client_e2e,
        mock_claude_agent,
        mock_notification_service
    ):
        """
        Scenario: Critical account automatically escalated to management.

        User Story: As a manager, I want to be immediately notified when
        an account reaches critical status.
        """
        # Arrange
        all_accounts = get_all_test_accounts()
        critical_accounts = get_high_risk_accounts(all_accounts, risk_threshold=85)
        manager_email = "director@company.com"
        account_owner_email = "manager1@company.com"

        # Act
        escalations = []
        for account in critical_accounts[:3]:
            # Analyze account
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            risk_analysis = await mock_claude_agent.query(
                f"Critical risk analysis {account['id']}",
                {"account": account_data, "priority": "critical"}
            )

            risk_score = account.get("Churn_Risk_Score", 0)

            # Escalate if critical
            if risk_score >= 85:
                escalation = {
                    "account_id": account["id"],
                    "account_name": account.get("Account_Name"),
                    "risk_score": risk_score,
                    "escalated_at": datetime.now(),
                    "reason": "Critical churn risk detected",
                    "analysis": risk_analysis
                }
                escalations.append(escalation)

                # Notify management
                await mock_notification_service.send_email(
                    to=manager_email,
                    subject=f"CRITICAL: Account Escalation - {account.get('Account_Name')}",
                    body=f"Account {account['id']} has reached critical status (Risk Score: {risk_score})"
                )

                # Notify account owner
                await mock_notification_service.send_email(
                    to=account_owner_email,
                    subject=f"Action Required: {account.get('Account_Name')}",
                    body=f"Your account has been escalated due to critical risk level."
                )

        # Assert
        assert len(escalations) > 0
        assert all(e["risk_score"] >= 85 for e in escalations)
        # Should have notifications for both manager and owner
        assert len(mock_notification_service.sent_notifications) >= len(escalations) * 2

    async def test_escalation_workflow_chain(
        self,
        mock_zoho_client_e2e,
        mock_notification_service
    ):
        """
        Scenario: Escalation follows chain of command.

        User Story: Critical accounts escalate through proper channels
        with appropriate notifications at each level.
        """
        # Arrange
        account = get_all_test_accounts()[0]
        escalation_chain = [
            {"role": "Account Manager", "email": "manager1@company.com", "level": 1},
            {"role": "Team Lead", "email": "teamlead@company.com", "level": 2},
            {"role": "Director", "email": "director@company.com", "level": 3},
            {"role": "VP", "email": "vp@company.com", "level": 4}
        ]

        # Act
        account_data = await mock_zoho_client_e2e.get_account(account["id"])
        risk_score = account.get("Churn_Risk_Score", 90)

        # Determine escalation level based on risk
        escalation_level = 1 if risk_score < 70 else \
                          2 if risk_score < 80 else \
                          3 if risk_score < 90 else 4

        # Notify everyone up to escalation level
        for person in escalation_chain[:escalation_level]:
            await mock_notification_service.send_email(
                to=person["email"],
                subject=f"Escalation Level {person['level']}: {account.get('Account_Name')}",
                body=f"Account requires attention at {person['role']} level."
            )

        # Assert
        assert len(mock_notification_service.sent_notifications) == escalation_level
        # Verify correct people notified
        notified_emails = [n["to"] for n in mock_notification_service.sent_notifications]
        expected_emails = [p["email"] for p in escalation_chain[:escalation_level]]
        assert notified_emails == expected_emails


# ============================================================================
# Test Suite: Approval/Rejection Scenario
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
class TestApprovalRejectionScenario:
    """Test approval workflow scenarios."""

    async def test_manager_approves_recommendation(
        self,
        mock_zoho_client_e2e,
        mock_claude_agent,
        mock_notification_service
    ):
        """
        Scenario: Manager approves recommended account changes.

        User Story: As an account manager, I want to review and approve
        recommended changes before they're applied to CRM.
        """
        # Arrange
        account = get_all_test_accounts()[0]
        manager_email = "manager1@company.com"
        approval_queue = []

        async def create_approval_request(account_id, changes, reasoning):
            request = {
                "id": f"approval_{len(approval_queue)}",
                "account_id": account_id,
                "proposed_changes": changes,
                "reasoning": reasoning,
                "status": "pending",
                "created_at": datetime.now()
            }
            approval_queue.append(request)
            return request["id"]

        async def approve_request(request_id, approver):
            for req in approval_queue:
                if req["id"] == request_id:
                    req["status"] = "approved"
                    req["approved_by"] = approver
                    req["approved_at"] = datetime.now()
                    return True
            return False

        # Act
        # 1. Generate recommendations
        account_data = await mock_zoho_client_e2e.get_account(account["id"])
        recommendations = await mock_claude_agent.query(
            f"Generate actionable recommendations for {account['id']}",
            {"account": account_data}
        )

        # 2. Create approval request
        proposed_changes = {
            "Rating": "Warm",
            "Next_Step": "Schedule QBR",
            "Notes": "Updated based on recent activity"
        }

        request_id = await create_approval_request(
            account["id"],
            proposed_changes,
            "AI-recommended based on engagement trends"
        )

        # 3. Notify manager for approval
        await mock_notification_service.send_email(
            to=manager_email,
            subject=f"Approval Required: {account.get('Account_Name')}",
            body=f"Please review and approve proposed changes for account {account['id']}"
        )

        # 4. Manager approves (simulated)
        approved = await approve_request(request_id, manager_email)

        # 5. Apply approved changes
        if approved:
            await mock_zoho_client_e2e.update_account(account["id"], proposed_changes)

            # Notify completion
            await mock_notification_service.send_email(
                to=manager_email,
                subject=f"Changes Applied: {account.get('Account_Name')}",
                body=f"Approved changes have been applied to account {account['id']}"
            )

        # Assert
        assert len(approval_queue) == 1
        assert approval_queue[0]["status"] == "approved"
        assert approval_queue[0]["approved_by"] == manager_email
        assert len(mock_notification_service.sent_notifications) == 2  # Request + Confirmation

    async def test_manager_rejects_recommendation(
        self,
        mock_zoho_client_e2e,
        mock_claude_agent,
        mock_cognee_client_e2e,
        mock_notification_service
    ):
        """
        Scenario: Manager rejects recommended changes with feedback.

        User Story: As an account manager, I want to reject recommendations
        and provide feedback to improve future suggestions.
        """
        # Arrange
        account = get_all_test_accounts()[0]
        manager_email = "manager1@company.com"
        approval_queue = []

        async def create_approval_request(account_id, changes):
            request = {
                "id": f"approval_{len(approval_queue)}",
                "account_id": account_id,
                "proposed_changes": changes,
                "status": "pending",
                "created_at": datetime.now()
            }
            approval_queue.append(request)
            return request["id"]

        async def reject_request(request_id, rejector, reason):
            for req in approval_queue:
                if req["id"] == request_id:
                    req["status"] = "rejected"
                    req["rejected_by"] = rejector
                    req["rejected_at"] = datetime.now()
                    req["rejection_reason"] = reason
                    return True
            return False

        # Act
        # 1. Generate recommendations
        account_data = await mock_zoho_client_e2e.get_account(account["id"])
        recommendations = await mock_claude_agent.query(
            f"Generate recommendations {account['id']}", {"account": account_data}
        )

        # 2. Create approval request
        proposed_changes = {"Rating": "Cold"}
        request_id = await create_approval_request(account["id"], proposed_changes)

        # 3. Manager rejects with reason
        rejection_reason = "Account is actually performing well, recent positive meeting not captured"
        rejected = await reject_request(request_id, manager_email, rejection_reason)

        # 4. Store feedback for learning
        if rejected:
            await mock_cognee_client_e2e.store(
                f"feedback_{request_id}",
                {
                    "account_id": account["id"],
                    "recommendation": proposed_changes,
                    "rejected": True,
                    "reason": rejection_reason,
                    "rejected_by": manager_email,
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Notify about rejection
            await mock_notification_service.send_slack(
                channel="#ai-feedback",
                message=f"Recommendation rejected for {account['id']}: {rejection_reason}"
            )

        # Assert
        assert len(approval_queue) == 1
        assert approval_queue[0]["status"] == "rejected"
        assert approval_queue[0]["rejection_reason"] == rejection_reason

        # Verify feedback stored
        feedback = await mock_cognee_client_e2e.get(f"feedback_{request_id}")
        assert feedback is not None
        assert feedback["rejected"] is True

    async def test_bulk_approval_workflow(
        self,
        mock_zoho_client_e2e,
        mock_notification_service
    ):
        """
        Scenario: Manager approves multiple recommendations at once.

        User Story: As an account manager, I want to batch approve
        multiple low-risk recommendations efficiently.
        """
        # Arrange
        accounts = get_all_test_accounts()[:10]
        manager_email = "manager1@company.com"
        approval_queue = []

        # Act
        # 1. Generate multiple approval requests
        for account in accounts:
            approval_queue.append({
                "id": f"approval_{len(approval_queue)}",
                "account_id": account["id"],
                "account_name": account.get("Account_Name"),
                "proposed_changes": {"Last_Review": datetime.now().isoformat()},
                "risk_level": "low",
                "status": "pending"
            })

        # 2. Filter low-risk approvals for bulk approval
        low_risk_approvals = [a for a in approval_queue if a["risk_level"] == "low"]

        # 3. Bulk approve
        for approval in low_risk_approvals:
            approval["status"] = "approved"
            approval["approved_by"] = manager_email
            approval["approved_at"] = datetime.now()

            # Apply changes
            await mock_zoho_client_e2e.update_account(
                approval["account_id"],
                approval["proposed_changes"]
            )

        # 4. Send summary notification
        await mock_notification_service.send_email(
            to=manager_email,
            subject=f"Bulk Approval Complete - {len(low_risk_approvals)} accounts updated",
            body=f"Successfully approved and applied changes to {len(low_risk_approvals)} accounts."
        )

        # Assert
        assert len(low_risk_approvals) == 10
        assert all(a["status"] == "approved" for a in low_risk_approvals)
        assert len(mock_notification_service.sent_notifications) == 1


# ============================================================================
# Test Suite: Performance Under Load
# ============================================================================

@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.slow
class TestPerformanceUnderLoad:
    """Test system performance under realistic load."""

    async def test_concurrent_user_sessions(
        self,
        mock_zoho_client_e2e,
        mock_claude_agent,
        mock_reporting_service
    ):
        """
        Scenario: Multiple users working simultaneously.

        Test system handles concurrent user sessions without degradation.
        """
        # Arrange
        users = [
            {"id": "owner_1", "accounts": 10},
            {"id": "owner_2", "accounts": 10},
            {"id": "owner_3", "accounts": 10},
            {"id": "owner_4", "accounts": 10},
            {"id": "owner_5", "accounts": 10}
        ]
        all_accounts = get_all_test_accounts()

        # Act
        start_time = datetime.now()

        async def simulate_user_session(user):
            user_accounts = get_accounts_by_owner(user["id"], all_accounts)[:user["accounts"]]

            analyses = []
            for account in user_accounts:
                account_data = await mock_zoho_client_e2e.get_account(account["id"])
                analysis = await mock_claude_agent.query(
                    f"Analyze {account['id']}", {"account": account_data}
                )
                analyses.append(analysis)

            brief = await mock_reporting_service.generate_owner_brief(
                user["id"], "daily", analyses
            )
            return brief

        # Simulate concurrent sessions
        briefs = await asyncio.gather(*[
            simulate_user_session(user) for user in users
        ])

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Assert
        assert len(briefs) == 5
        assert all(brief["accounts_reviewed"] > 0 for brief in briefs)
        # Should handle 5 concurrent users efficiently
        assert duration < 120  # Complete in under 2 minutes

    async def test_peak_load_handling(
        self,
        mock_zoho_client_e2e,
        mock_claude_agent
    ):
        """
        Scenario: System under peak morning load.

        Test system handles peak load when all managers receive
        their morning briefs simultaneously.
        """
        # Arrange
        all_accounts = get_all_test_accounts()

        # Act
        start_time = datetime.now()

        # Simulate peak load: 50 accounts analyzed simultaneously
        async def quick_analysis(account):
            account_data = await mock_zoho_client_e2e.get_account(account["id"])
            return await mock_claude_agent.query(
                f"Quick analysis {account['id']}", {"account": account_data}
            )

        results = await asyncio.gather(*[
            quick_analysis(acc) for acc in all_accounts
        ])

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Assert
        assert len(results) == len(all_accounts)
        # Should handle peak load efficiently
        assert duration < 180  # Complete 50 accounts in under 3 minutes
        # Calculate throughput
        throughput = len(all_accounts) / duration
        assert throughput > 0.25  # At least 15 accounts per minute
