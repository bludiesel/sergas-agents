"""Email and task templates for recommendation author.

This module provides Jinja2-based templates for generating personalized
emails and task descriptions based on different scenarios.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from jinja2 import Environment, Template, select_autoescape
import structlog

from .recommendation_models import (
    EmailDraft,
    Priority,
    RecommendationType,
    TaskSuggestion
)

logger = structlog.get_logger()


# Email template definitions
EMAIL_TEMPLATES = {
    "follow_up_no_activity": """Subject: Checking in on {{ account_name }}

Hi {{ contact_name }},

I hope this message finds you well. I wanted to reach out as it's been {{ days_since_activity }} days since we last connected.

I wanted to check in and see how things are progressing on your end. {% if last_discussion_topic %}When we last spoke about {{ last_discussion_topic }}, {% else %}In our previous conversations, {% endif %}you mentioned {{ key_points }}.

I'd love to reconnect and discuss:
{% for point in discussion_points %}
- {{ point }}
{% endfor %}

Would you have 15-20 minutes for a quick call this week? I'm available {{ availability }}.

Looking forward to hearing from you.

Best regards,
{{ sender_name }}""",

    "deal_at_risk": """Subject: Partnership status for {{ account_name }}

Hi {{ contact_name }},

I wanted to reach out regarding our ongoing {{ deal_name }} opportunity, which has been in {{ deal_stage }} stage for {{ days_stalled }} days.

I understand that complex decisions take time, and I want to ensure we're aligned on next steps and addressing any concerns you may have.

{% if blockers %}I'm aware of some potential blockers:
{% for blocker in blockers %}
- {{ blocker }}
{% endfor %}
{% endif %}

Could we schedule a brief call to:
1. Review current status and timeline
2. Address any questions or concerns
3. Determine the best path forward

I'm committed to ensuring this partnership delivers value for {{ account_name }}. Please let me know what works for your schedule.

Best regards,
{{ sender_name }}""",

    "renewal_reminder": """Subject: {{ account_name }} renewal timeline

Hi {{ contact_name }},

I wanted to reach out regarding your upcoming renewal, scheduled for {{ renewal_date }}. With {{ days_until_renewal }} days remaining, I wanted to ensure we have ample time to discuss your experience and future plans.

Over the past year, I've enjoyed seeing {{ account_name }} {{ accomplishments }}.

I'd like to schedule time to:
1. Review your current usage and satisfaction
2. Discuss any evolving needs or goals
3. Explore options for the renewal period
4. Address any questions or concerns

Would you be available for a {{ meeting_duration }}-minute call next week? I have availability on {{ suggested_times }}.

Looking forward to continuing our partnership.

Best regards,
{{ sender_name }}""",

    "upsell_opportunity": """Subject: Potential opportunity for {{ account_name }}

Hi {{ contact_name }},

I hope you're doing well! I've been reviewing how {{ account_name }} is using our solution, and I noticed some patterns that suggest {{ opportunity_description }}.

Based on {{ data_points }}, I believe there's an opportunity to {{ value_proposition }}.

Companies similar to {{ account_name }} have seen:
{% for benefit in benefits %}
- {{ benefit }}
{% endfor %}

I'd love to schedule a brief exploratory conversation to see if this might be valuable for your team. No pressure—just exploring possibilities.

Would you have 20 minutes for a call {{ timeframe }}?

Best regards,
{{ sender_name }}""",

    "executive_alignment": """Subject: Strategic partnership review - {{ account_name }}

Hi {{ executive_name }},

I hope this message finds you well. As {{ account_name }}'s {{ executive_title }}, I wanted to reach out to ensure our partnership continues to align with your strategic priorities.

{{ current_state_summary }}

I believe there are opportunities to {{ strategic_value }} and I'd welcome the chance to discuss:
1. Your current priorities and initiatives
2. How our partnership can better support your goals
3. Strategic expansion opportunities

Would you be available for a {{ meeting_duration }}-minute executive briefing in the coming weeks? I'm happy to work around your schedule.

Looking forward to the conversation.

Best regards,
{{ sender_name }}
{{ sender_title }}""",

    "re_engagement": """Subject: Reconnecting with {{ account_name }}

Hi {{ contact_name }},

I hope you're doing well! It's been a while since we last connected, and I wanted to reach out with some updates that might be relevant to {{ account_name }}.

We've recently {{ recent_developments }}, which {% if industry %}companies in the {{ industry }} space{% else %}many of our clients{% endif %} have found valuable.

I'd love to reconnect and hear:
- How things are going on your end
- What your current priorities are
- Whether there are ways we can support your goals

No sales pitch—just genuinely interested in reconnecting and seeing if there's anything useful we can share.

Would you have 15 minutes for a casual catch-up call {{ timeframe }}?

Best regards,
{{ sender_name }}"""
}


TASK_TEMPLATES = {
    "follow_up_call": {
        "title": "Follow-up call: {{ account_name }}",
        "description": """Call {{ contact_name }} at {{ account_name }} to discuss:

{% if purpose %}Purpose: {{ purpose }}
{% endif %}
Key topics:
{% for topic in topics %}
- {{ topic }}
{% endfor %}

{% if preparation_notes %}Preparation notes:
{{ preparation_notes }}
{% endif %}

Expected outcome: {{ expected_outcome }}

Contact: {{ contact_phone }}{% if contact_email %} / {{ contact_email }}{% endif %}""",
        "estimated_hours": 0.5
    },

    "send_proposal": {
        "title": "Send proposal: {{ deal_name }} - {{ account_name }}",
        "description": """Prepare and send proposal for {{ deal_name }}.

Requirements:
{% for req in requirements %}
- {{ req }}
{% endfor %}

Deliverables:
{% for deliverable in deliverables %}
- {{ deliverable }}
{% endfor %}

Timeline: {{ proposal_timeline }}
Value: {{ deal_value }}

Next step: {{ next_step }}""",
        "estimated_hours": 2.0
    },

    "schedule_meeting": {
        "title": "Schedule meeting: {{ meeting_type }} with {{ account_name }}",
        "description": """Schedule {{ meeting_type }} with {{ attendees }}.

Agenda:
{% for item in agenda_items %}
- {{ item }}
{% endfor %}

{% if preparation_required %}Preparation required:
{{ preparation_required }}
{% endif %}

Duration: {{ duration }} minutes
Preferred times: {{ preferred_times }}""",
        "estimated_hours": 0.25
    },

    "escalate_to_manager": {
        "title": "ESCALATION: {{ account_name }} - {{ escalation_reason }}",
        "description": """PRIORITY: {{ priority }}

Account: {{ account_name }}
Issue: {{ escalation_reason }}

Context:
{{ context }}

Recommended actions:
{% for action in recommended_actions %}
- {{ action }}
{% endfor %}

Risk if not addressed: {{ risk_description }}

Timeline: {{ timeline }}""",
        "estimated_hours": 1.0
    },

    "update_crm": {
        "title": "Update CRM: {{ account_name }}",
        "description": """Update CRM records for {{ account_name }}.

Updates needed:
{% for field, value in updates.items %}
- {{ field }}: {{ value }}
{% endfor %}

{% if notes %}Additional notes:
{{ notes }}
{% endif %}

Reason: {{ reason }}""",
        "estimated_hours": 0.25
    }
}


class TemplateRenderer:
    """Renders email and task templates with personalization."""

    def __init__(self) -> None:
        """Initialize template renderer with Jinja2 environment."""
        self.env = Environment(
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.logger = logger.bind(component="template_renderer")

    def render_email_template(
        self,
        template_key: str,
        variables: Dict[str, Any]
    ) -> EmailDraft:
        """Render email template with variables.

        Args:
            template_key: Template identifier
            variables: Template variables

        Returns:
            EmailDraft with rendered content

        Raises:
            ValueError: If template not found
        """
        if template_key not in EMAIL_TEMPLATES:
            raise ValueError(f"Email template '{template_key}' not found")

        template_str = EMAIL_TEMPLATES[template_key]
        template = self.env.from_string(template_str)

        # Ensure required variables
        variables = self._ensure_email_variables(variables, template_key)

        # Render template
        rendered = template.render(**variables)

        # Extract subject and body
        lines = rendered.strip().split('\n', 1)
        subject = lines[0].replace('Subject:', '').strip()
        body = lines[1].strip() if len(lines) > 1 else ""

        # Create email draft
        return EmailDraft(
            subject=subject,
            body=body,
            to_contacts=variables.get('to_contacts', [variables.get('contact_email', '')]),
            cc_contacts=variables.get('cc_contacts', []),
            template_id=template_key,
            personalization_fields=variables,
            tone=variables.get('tone', 'professional'),
            urgency=variables.get('urgency', Priority.MEDIUM)
        )

    def render_task_template(
        self,
        template_key: str,
        variables: Dict[str, Any]
    ) -> TaskSuggestion:
        """Render task template with variables.

        Args:
            template_key: Template identifier
            variables: Template variables

        Returns:
            TaskSuggestion with rendered content

        Raises:
            ValueError: If template not found
        """
        if template_key not in TASK_TEMPLATES:
            raise ValueError(f"Task template '{template_key}' not found")

        template_config = TASK_TEMPLATES[template_key]

        # Render title
        title_template = self.env.from_string(template_config['title'])
        title = title_template.render(**variables)

        # Render description
        desc_template = self.env.from_string(template_config['description'])
        description = desc_template.render(**variables)

        # Calculate due date
        priority = variables.get('priority', Priority.MEDIUM)
        due_date = self._calculate_due_date(priority)

        # Create task suggestion
        return TaskSuggestion(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            assigned_to=variables.get('assigned_to'),
            related_to={
                'account_id': variables.get('account_id', ''),
                'deal_id': variables.get('deal_id', '')
            },
            task_type=template_key,
            estimated_hours=template_config.get('estimated_hours', 1.0)
        )

    def _ensure_email_variables(
        self,
        variables: Dict[str, Any],
        template_key: str
    ) -> Dict[str, Any]:
        """Ensure all required email variables are present.

        Args:
            variables: Current variables
            template_key: Template identifier

        Returns:
            Variables with defaults added
        """
        defaults = {
            'contact_name': 'there',
            'account_name': 'your organization',
            'sender_name': 'Account Manager',
            'sender_title': 'Account Executive',
            'timeframe': 'this week',
            'availability': 'most days this week',
            'meeting_duration': '30'
        }

        # Template-specific defaults
        if template_key == 'follow_up_no_activity':
            defaults.update({
                'days_since_activity': '14',
                'key_points': 'your goals for this quarter',
                'discussion_points': ['Current progress and priorities', 'Any support needed']
            })
        elif template_key == 'renewal_reminder':
            days_until = variables.get('days_until_renewal', 30)
            renewal_date = (datetime.now() + timedelta(days=days_until)).strftime('%B %d, %Y')
            defaults.update({
                'renewal_date': renewal_date,
                'days_until_renewal': str(days_until),
                'accomplishments': 'grow and achieve your goals',
                'suggested_times': 'Tuesday or Thursday afternoon'
            })

        # Merge with provided variables (provided values take precedence)
        result = {**defaults, **variables}
        return result

    def _calculate_due_date(self, priority: Priority) -> datetime:
        """Calculate task due date based on priority.

        Args:
            priority: Task priority

        Returns:
            Due date datetime
        """
        now = datetime.utcnow()

        if priority == Priority.CRITICAL:
            return now + timedelta(hours=24)
        elif priority == Priority.HIGH:
            return now + timedelta(days=2)
        elif priority == Priority.MEDIUM:
            return now + timedelta(days=7)
        else:  # LOW
            return now + timedelta(days=14)

    def get_template_variables(self, template_key: str) -> List[str]:
        """Get list of variables used in a template.

        Args:
            template_key: Template identifier

        Returns:
            List of variable names

        Raises:
            ValueError: If template not found
        """
        if template_key in EMAIL_TEMPLATES:
            template_str = EMAIL_TEMPLATES[template_key]
        elif template_key in TASK_TEMPLATES:
            config = TASK_TEMPLATES[template_key]
            template_str = config['title'] + '\n' + config['description']
        else:
            raise ValueError(f"Template '{template_key}' not found")

        # Parse template to extract variables
        template = self.env.from_string(template_str)
        variables = template.module.__dict__.get('variables', set())

        return list(variables)


def select_email_template(
    recommendation_type: RecommendationType,
    context: Dict[str, Any]
) -> str:
    """Select appropriate email template based on recommendation type and context.

    Args:
        recommendation_type: Type of recommendation
        context: Context information for selection

    Returns:
        Template key
    """
    # Direct mappings
    template_map = {
        RecommendationType.FOLLOW_UP_EMAIL: 'follow_up_no_activity',
        RecommendationType.RENEWAL_REMINDER: 'renewal_reminder',
        RecommendationType.UPSELL_OPPORTUNITY: 'upsell_opportunity',
        RecommendationType.EXECUTIVE_ALIGNMENT: 'executive_alignment',
        RecommendationType.RE_ENGAGEMENT: 're_engagement'
    }

    if recommendation_type in template_map:
        return template_map[recommendation_type]

    # Context-based selection
    if context.get('deal_stalled'):
        return 'deal_at_risk'

    # Default
    return 'follow_up_no_activity'


def select_task_template(
    action_type: str,
    context: Dict[str, Any]
) -> str:
    """Select appropriate task template based on action type.

    Args:
        action_type: Type of action
        context: Context information

    Returns:
        Template key
    """
    action_map = {
        'call': 'follow_up_call',
        'phone': 'follow_up_call',
        'proposal': 'send_proposal',
        'meeting': 'schedule_meeting',
        'schedule': 'schedule_meeting',
        'escalate': 'escalate_to_manager',
        'update': 'update_crm'
    }

    action_lower = action_type.lower()
    for key, template in action_map.items():
        if key in action_lower:
            return template

    # Default
    return 'follow_up_call'


def get_available_templates() -> Dict[str, List[str]]:
    """Get list of available templates.

    Returns:
        Dictionary with email and task template keys
    """
    return {
        'email_templates': list(EMAIL_TEMPLATES.keys()),
        'task_templates': list(TASK_TEMPLATES.keys())
    }
