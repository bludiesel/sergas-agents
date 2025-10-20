"""Comprehensive tests for recommendation templates.

Tests email templates, task templates, and template rendering with Jinja2.
"""

import pytest
from datetime import datetime, timedelta
from typing import Any, Dict

from src.agents.recommendation_templates import (
    EMAIL_TEMPLATES,
    TASK_TEMPLATES,
    TemplateRenderer,
    get_available_templates,
    select_email_template,
    select_task_template,
)
from src.agents.recommendation_models import (
    EmailDraft,
    Priority,
    RecommendationType,
    TaskSuggestion,
)


class TestEmailTemplates:
    """Tests for email template content and structure."""

    def test_all_email_templates_exist(self):
        """Test that all expected email templates are defined."""
        expected_templates = [
            "follow_up_no_activity",
            "deal_at_risk",
            "renewal_reminder",
            "upsell_opportunity",
            "executive_alignment",
            "re_engagement"
        ]

        for template in expected_templates:
            assert template in EMAIL_TEMPLATES

    def test_email_template_has_subject(self):
        """Test that all email templates have Subject line."""
        for template_key, template_content in EMAIL_TEMPLATES.items():
            assert "Subject:" in template_content, f"Template {template_key} missing Subject"

    def test_email_template_has_greeting(self):
        """Test that templates include contact_name variable."""
        for template_key, template_content in EMAIL_TEMPLATES.items():
            assert "{{ contact_name }}" in template_content or "Hi" in template_content

    def test_follow_up_template_variables(self):
        """Test follow_up_no_activity template has expected variables."""
        template = EMAIL_TEMPLATES["follow_up_no_activity"]
        assert "{{ account_name }}" in template
        assert "{{ days_since_activity }}" in template
        assert "{{ sender_name }}" in template

    def test_deal_at_risk_template_variables(self):
        """Test deal_at_risk template has expected variables."""
        template = EMAIL_TEMPLATES["deal_at_risk"]
        assert "{{ deal_name }}" in template
        assert "{{ deal_stage }}" in template
        assert "{{ days_stalled }}" in template
        assert "{% if blockers %}" in template

    def test_renewal_reminder_template_variables(self):
        """Test renewal_reminder template has expected variables."""
        template = EMAIL_TEMPLATES["renewal_reminder"]
        assert "{{ renewal_date }}" in template
        assert "{{ days_until_renewal }}" in template
        assert "{{ accomplishments }}" in template

    def test_upsell_opportunity_template_variables(self):
        """Test upsell_opportunity template has expected variables."""
        template = EMAIL_TEMPLATES["upsell_opportunity"]
        assert "{{ opportunity_description }}" in template
        assert "{{ value_proposition }}" in template
        assert "{% for benefit in benefits %}" in template

    def test_executive_alignment_template_variables(self):
        """Test executive_alignment template has expected variables."""
        template = EMAIL_TEMPLATES["executive_alignment"]
        assert "{{ executive_name }}" in template
        assert "{{ executive_title }}" in template
        assert "{{ current_state_summary }}" in template

    def test_re_engagement_template_variables(self):
        """Test re_engagement template has expected variables."""
        template = EMAIL_TEMPLATES["re_engagement"]
        assert "{{ recent_developments }}" in template
        assert "{% if industry %}" in template


class TestTaskTemplates:
    """Tests for task template content and structure."""

    def test_all_task_templates_exist(self):
        """Test that all expected task templates are defined."""
        expected_templates = [
            "follow_up_call",
            "send_proposal",
            "schedule_meeting",
            "escalate_to_manager",
            "update_crm"
        ]

        for template in expected_templates:
            assert template in TASK_TEMPLATES

    def test_task_template_has_title(self):
        """Test that all task templates have title field."""
        for template_key, template_config in TASK_TEMPLATES.items():
            assert "title" in template_config, f"Template {template_key} missing title"

    def test_task_template_has_description(self):
        """Test that all task templates have description field."""
        for template_key, template_config in TASK_TEMPLATES.items():
            assert "description" in template_config

    def test_task_template_has_estimated_hours(self):
        """Test that all task templates have estimated_hours."""
        for template_key, template_config in TASK_TEMPLATES.items():
            assert "estimated_hours" in template_config
            assert isinstance(template_config["estimated_hours"], (int, float))

    def test_follow_up_call_template(self):
        """Test follow_up_call task template structure."""
        template = TASK_TEMPLATES["follow_up_call"]
        assert "{{ account_name }}" in template["title"]
        assert "{{ contact_name }}" in template["description"]
        assert template["estimated_hours"] == 0.5

    def test_send_proposal_template(self):
        """Test send_proposal task template structure."""
        template = TASK_TEMPLATES["send_proposal"]
        assert "{{ deal_name }}" in template["title"]
        assert "{% for req in requirements %}" in template["description"]
        assert template["estimated_hours"] == 2.0

    def test_schedule_meeting_template(self):
        """Test schedule_meeting task template structure."""
        template = TASK_TEMPLATES["schedule_meeting"]
        assert "{{ meeting_type }}" in template["title"]
        assert "{% for item in agenda_items %}" in template["description"]
        assert template["estimated_hours"] == 0.25

    def test_escalate_to_manager_template(self):
        """Test escalate_to_manager task template structure."""
        template = TASK_TEMPLATES["escalate_to_manager"]
        assert "ESCALATION" in template["title"]
        assert "{{ escalation_reason }}" in template["title"]
        assert "PRIORITY" in template["description"]
        assert template["estimated_hours"] == 1.0

    def test_update_crm_template(self):
        """Test update_crm task template structure."""
        template = TASK_TEMPLATES["update_crm"]
        assert "Update CRM" in template["title"]
        assert "{% for field, value in updates.items %}" in template["description"]
        assert template["estimated_hours"] == 0.25


class TestTemplateRenderer:
    """Tests for TemplateRenderer class."""

    @pytest.fixture
    def renderer(self) -> TemplateRenderer:
        """Create a TemplateRenderer instance."""
        return TemplateRenderer()

    # Email Template Rendering Tests
    def test_render_follow_up_email_template(self, renderer: TemplateRenderer):
        """Test rendering follow_up_no_activity email template."""
        variables = {
            "contact_name": "John Smith",
            "account_name": "Acme Corp",
            "days_since_activity": "30",
            "key_points": "expanding to new regions",
            "discussion_points": ["Q4 expansion plans", "Technical requirements"],
            "sender_name": "Jane Doe",
            "to_contacts": ["john@acme.com"]
        }

        email = renderer.render_email_template("follow_up_no_activity", variables)

        assert isinstance(email, EmailDraft)
        assert "Acme Corp" in email.subject
        assert "John Smith" in email.body
        assert "30 days" in email.body
        assert email.to_contacts == ["john@acme.com"]

    def test_render_deal_at_risk_template(self, renderer: TemplateRenderer):
        """Test rendering deal_at_risk email template."""
        variables = {
            "contact_name": "Alice Johnson",
            "account_name": "TechStart Inc",
            "deal_name": "Enterprise License",
            "deal_stage": "Negotiation",
            "days_stalled": "45",
            "blockers": ["Budget approval pending", "Security review needed"],
            "sender_name": "Bob Manager",
            "to_contacts": ["alice@techstart.com"]
        }

        email = renderer.render_email_template("deal_at_risk", variables)

        assert "TechStart Inc" in email.subject or "TechStart Inc" in email.body
        assert "Enterprise License" in email.body
        assert "45 days" in email.body
        assert "Budget approval pending" in email.body

    def test_render_renewal_reminder_template(self, renderer: TemplateRenderer):
        """Test rendering renewal_reminder email template."""
        variables = {
            "contact_name": "Carlos Rodriguez",
            "account_name": "Global Systems",
            "days_until_renewal": "30",
            "accomplishments": "increased productivity by 40%",
            "sender_name": "Sarah Sales",
            "to_contacts": ["carlos@globalsystems.com"]
        }

        email = renderer.render_email_template("renewal_reminder", variables)

        assert "renewal" in email.subject.lower()
        assert "Global Systems" in email.body
        assert "30 days" in email.body or "30" in email.body

    def test_render_upsell_opportunity_template(self, renderer: TemplateRenderer):
        """Test rendering upsell_opportunity email template."""
        variables = {
            "contact_name": "Diana Lee",
            "account_name": "Innovation Labs",
            "opportunity_description": "expanded feature usage would benefit your team",
            "data_points": "increased API calls by 200%",
            "value_proposition": "improve efficiency by 50%",
            "benefits": ["Faster processing", "Better analytics", "Cost savings"],
            "sender_name": "Tom Account Manager",
            "to_contacts": ["diana@innovationlabs.com"]
        }

        email = renderer.render_email_template("upsell_opportunity", variables)

        assert "opportunity" in email.subject.lower() or "Innovation Labs" in email.subject
        assert "Faster processing" in email.body
        assert "Better analytics" in email.body

    def test_render_executive_alignment_template(self, renderer: TemplateRenderer):
        """Test rendering executive_alignment email template."""
        variables = {
            "executive_name": "Michael Chen",
            "executive_title": "CTO",
            "account_name": "Enterprise Co",
            "current_state_summary": "Strong engagement with engineering team",
            "strategic_value": "enhance your digital transformation initiatives",
            "sender_name": "Lisa Executive",
            "sender_title": "VP of Customer Success",
            "to_contacts": ["michael.chen@enterprise.com"]
        }

        email = renderer.render_email_template("executive_alignment", variables)

        assert "Strategic" in email.subject or "Enterprise Co" in email.subject
        assert "CTO" in email.body
        assert "digital transformation" in email.body

    def test_render_re_engagement_template(self, renderer: TemplateRenderer):
        """Test rendering re_engagement email template."""
        variables = {
            "contact_name": "Olivia Martinez",
            "account_name": "Digital Partners",
            "recent_developments": "launched new AI-powered features",
            "industry": "fintech",
            "sender_name": "Paul Manager",
            "to_contacts": ["olivia@digitalpartners.com"]
        }

        email = renderer.render_email_template("re_engagement", variables)

        assert "Digital Partners" in email.subject or "Reconnecting" in email.subject
        assert "AI-powered features" in email.body
        assert "fintech" in email.body

    def test_email_template_with_defaults(self, renderer: TemplateRenderer):
        """Test that renderer adds default values for missing variables."""
        variables = {
            "to_contacts": ["test@example.com"]
        }

        email = renderer.render_email_template("follow_up_no_activity", variables)

        # Should use defaults
        assert len(email.body) > 50  # Valid body
        assert email.tone == "professional"
        assert email.urgency == Priority.MEDIUM

    def test_email_template_invalid_template_key(self, renderer: TemplateRenderer):
        """Test error handling for invalid template key."""
        with pytest.raises(ValueError, match="Email template .* not found"):
            renderer.render_email_template("nonexistent_template", {})

    def test_email_personalization_fields_stored(self, renderer: TemplateRenderer):
        """Test that personalization fields are stored in EmailDraft."""
        variables = {
            "contact_name": "Test User",
            "account_name": "Test Corp",
            "to_contacts": ["test@example.com"]
        }

        email = renderer.render_email_template("follow_up_no_activity", variables)

        assert email.personalization_fields["contact_name"] == "Test User"
        assert email.template_id == "follow_up_no_activity"

    # Task Template Rendering Tests
    def test_render_follow_up_call_task(self, renderer: TemplateRenderer):
        """Test rendering follow_up_call task template."""
        variables = {
            "account_name": "Acme Corp",
            "contact_name": "John Smith",
            "purpose": "Discuss renewal options",
            "topics": ["Pricing", "New features", "Timeline"],
            "expected_outcome": "Agreement on next steps",
            "contact_phone": "555-0123",
            "contact_email": "john@acme.com",
            "account_id": "123",
            "priority": Priority.HIGH
        }

        task = renderer.render_task_template("follow_up_call", variables)

        assert isinstance(task, TaskSuggestion)
        assert "Acme Corp" in task.title
        assert "John Smith" in task.description
        assert "Pricing" in task.description
        assert task.estimated_hours == 0.5

    def test_render_send_proposal_task(self, renderer: TemplateRenderer):
        """Test rendering send_proposal task template."""
        variables = {
            "deal_name": "Enterprise License",
            "account_name": "TechCo",
            "requirements": ["Detailed pricing", "Implementation timeline", "Support SLA"],
            "deliverables": ["Proposal document", "ROI analysis"],
            "proposal_timeline": "Within 3 business days",
            "deal_value": "$150,000",
            "next_step": "Schedule review meeting",
            "account_id": "456"
        }

        task = renderer.render_task_template("send_proposal", variables)

        assert "Enterprise License" in task.title
        assert "Detailed pricing" in task.description
        assert task.estimated_hours == 2.0

    def test_render_schedule_meeting_task(self, renderer: TemplateRenderer):
        """Test rendering schedule_meeting task template."""
        variables = {
            "meeting_type": "Quarterly Business Review",
            "account_name": "BigClient Inc",
            "attendees": "CTO and VP Engineering",
            "agenda_items": ["Review Q3 results", "Discuss Q4 goals", "Feature requests"],
            "duration": "60",
            "preferred_times": "Tuesday or Wednesday afternoon",
            "account_id": "789"
        }

        task = renderer.render_task_template("schedule_meeting", variables)

        assert "Quarterly Business Review" in task.title
        assert "Review Q3 results" in task.description
        assert task.estimated_hours == 0.25

    def test_render_escalate_to_manager_task(self, renderer: TemplateRenderer):
        """Test rendering escalate_to_manager task template."""
        variables = {
            "account_name": "Critical Account",
            "escalation_reason": "Churn Risk",
            "priority": Priority.CRITICAL,
            "context": "Customer expressed dissatisfaction with recent changes",
            "recommended_actions": ["Executive call within 24h", "Offer concessions"],
            "risk_description": "Loss of $500K annual contract",
            "timeline": "Immediate",
            "account_id": "999"
        }

        task = renderer.render_task_template("escalate_to_manager", variables)

        assert "ESCALATION" in task.title
        assert "Churn Risk" in task.title
        assert "CRITICAL" in task.description
        assert task.estimated_hours == 1.0

    def test_render_update_crm_task(self, renderer: TemplateRenderer):
        """Test rendering update_crm task template."""
        variables = {
            "account_name": "Test Account",
            "updates": {
                "Health Score": "Yellow",
                "Next Review Date": "2024-03-01",
                "Notes": "Customer requested feature demo"
            },
            "reason": "Quarterly review completed",
            "account_id": "111"
        }

        task = renderer.render_task_template("update_crm", variables)

        assert "Update CRM" in task.title
        assert "Health Score" in task.description
        assert task.estimated_hours == 0.25

    def test_task_due_date_calculation_critical(self, renderer: TemplateRenderer):
        """Test due date calculation for critical priority."""
        variables = {
            "account_name": "Test",
            "priority": Priority.CRITICAL,
            "account_id": "123",
            "contact_name": "Test User",
            "topics": ["Test"],
            "expected_outcome": "Test",
            "contact_phone": "555-0000"
        }

        before = datetime.utcnow()
        task = renderer.render_task_template("follow_up_call", variables)
        after = datetime.utcnow()

        # Due within 24 hours
        assert task.due_date <= after + timedelta(hours=25)
        assert task.due_date >= before + timedelta(hours=23)

    def test_task_due_date_calculation_high(self, renderer: TemplateRenderer):
        """Test due date calculation for high priority."""
        variables = {
            "account_name": "Test",
            "priority": Priority.HIGH,
            "account_id": "123",
            "contact_name": "Test User",
            "topics": ["Test"],
            "expected_outcome": "Test",
            "contact_phone": "555-0000"
        }

        task = renderer.render_task_template("follow_up_call", variables)

        # Due within 2 days
        assert task.due_date <= datetime.utcnow() + timedelta(days=3)

    def test_task_invalid_template_key(self, renderer: TemplateRenderer):
        """Test error handling for invalid task template key."""
        with pytest.raises(ValueError, match="Task template .* not found"):
            renderer.render_task_template("nonexistent_task", {})

    def test_task_related_to_populated(self, renderer: TemplateRenderer):
        """Test that related_to is populated correctly."""
        variables = {
            "account_name": "Test",
            "account_id": "123",
            "deal_id": "456",
            "contact_name": "Test User",
            "topics": ["Test"],
            "expected_outcome": "Test",
            "contact_phone": "555-0000"
        }

        task = renderer.render_task_template("follow_up_call", variables)

        assert task.related_to["account_id"] == "123"
        assert task.related_to["deal_id"] == "456"


class TestTemplateSelectorFunctions:
    """Tests for template selector helper functions."""

    def test_select_email_template_follow_up(self):
        """Test selecting email template for follow_up."""
        template = select_email_template(
            RecommendationType.FOLLOW_UP_EMAIL,
            {}
        )
        assert template == "follow_up_no_activity"

    def test_select_email_template_renewal(self):
        """Test selecting email template for renewal."""
        template = select_email_template(
            RecommendationType.RENEWAL_REMINDER,
            {}
        )
        assert template == "renewal_reminder"

    def test_select_email_template_upsell(self):
        """Test selecting email template for upsell."""
        template = select_email_template(
            RecommendationType.UPSELL_OPPORTUNITY,
            {}
        )
        assert template == "upsell_opportunity"

    def test_select_email_template_executive(self):
        """Test selecting email template for executive alignment."""
        template = select_email_template(
            RecommendationType.EXECUTIVE_ALIGNMENT,
            {}
        )
        assert template == "executive_alignment"

    def test_select_email_template_re_engagement(self):
        """Test selecting email template for re-engagement."""
        template = select_email_template(
            RecommendationType.RE_ENGAGEMENT,
            {}
        )
        assert template == "re_engagement"

    def test_select_email_template_deal_stalled_context(self):
        """Test selecting template based on context."""
        template = select_email_template(
            RecommendationType.SCHEDULE_MEETING,
            {"deal_stalled": True}
        )
        assert template == "deal_at_risk"

    def test_select_email_template_default(self):
        """Test default email template selection."""
        template = select_email_template(
            RecommendationType.CREATE_TASK,
            {}
        )
        assert template == "follow_up_no_activity"

    def test_select_task_template_call(self):
        """Test selecting task template for call."""
        template = select_task_template("call", {})
        assert template == "follow_up_call"

        template = select_task_template("phone", {})
        assert template == "follow_up_call"

    def test_select_task_template_proposal(self):
        """Test selecting task template for proposal."""
        template = select_task_template("proposal", {})
        assert template == "send_proposal"

    def test_select_task_template_meeting(self):
        """Test selecting task template for meeting."""
        template = select_task_template("meeting", {})
        assert template == "schedule_meeting"

        template = select_task_template("schedule", {})
        assert template == "schedule_meeting"

    def test_select_task_template_escalate(self):
        """Test selecting task template for escalation."""
        template = select_task_template("escalate", {})
        assert template == "escalate_to_manager"

    def test_select_task_template_update(self):
        """Test selecting task template for CRM update."""
        template = select_task_template("update", {})
        assert template == "update_crm"

    def test_select_task_template_default(self):
        """Test default task template selection."""
        template = select_task_template("unknown_action", {})
        assert template == "follow_up_call"

    def test_get_available_templates(self):
        """Test getting list of available templates."""
        templates = get_available_templates()

        assert "email_templates" in templates
        assert "task_templates" in templates
        assert len(templates["email_templates"]) == 6
        assert len(templates["task_templates"]) == 5
        assert "follow_up_no_activity" in templates["email_templates"]
        assert "follow_up_call" in templates["task_templates"]
