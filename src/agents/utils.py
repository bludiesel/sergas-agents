"""Data Scout Agent - Utility Functions.

Change detection, risk assessment, and data aggregation utilities
following SPARC pseudocode specifications (lines 574-657).

All functions with:
- Complete implementation
- Type hints
- Error handling
- Performance optimization
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import structlog

from src.agents.models import (
    FieldChange,
    ChangeType,
    DealRecord,
    ActivityRecord,
    AccountRecord,
    RiskSignal,
    RiskLevel,
    DealStage,
    ActivityType,
)

logger = structlog.get_logger(__name__)


# ============================================================================
# CHANGE DETECTION UTILITIES
# ============================================================================

def calculate_field_diff(
    old_data: Dict[str, Any],
    new_data: Dict[str, Any],
    ignore_fields: Optional[List[str]] = None,
) -> List[FieldChange]:
    """Calculate field-level differences between old and new data.

    Algorithm from pseudocode lines 574-629.

    Args:
        old_data: Previous state
        new_data: Current state
        ignore_fields: Fields to skip in comparison

    Returns:
        List of detected field changes
    """
    if ignore_fields is None:
        ignore_fields = ["Modified_Time", "Last_Modified_Time", "$approval_state"]

    changes: List[FieldChange] = []

    # Find modified fields
    all_fields = set(old_data.keys()) | set(new_data.keys())

    for field in all_fields:
        if field in ignore_fields:
            continue

        old_value = old_data.get(field)
        new_value = new_data.get(field)

        # Skip if values are same
        if old_value == new_value:
            continue

        # Determine change type
        change_type = _classify_field_change(field, old_value, new_value)

        if change_type:
            change = FieldChange(
                field_name=field,
                old_value=old_value,
                new_value=new_value,
                timestamp=datetime.utcnow(),
                change_type=change_type,
            )
            changes.append(change)

    logger.info(
        "field_diff_calculated",
        changes_detected=len(changes),
        fields_compared=len(all_fields),
    )

    return changes


def _classify_field_change(
    field_name: str,
    old_value: Any,
    new_value: Any,
) -> Optional[ChangeType]:
    """Classify type of field change.

    Args:
        field_name: Field that changed
        old_value: Previous value
        new_value: New value

    Returns:
        Change type classification
    """
    field_lower = field_name.lower()

    # Owner change
    if "owner" in field_lower:
        return ChangeType.OWNER_CHANGE

    # Status change
    if "status" in field_lower or "account_status" in field_lower:
        return ChangeType.STATUS_CHANGE

    # Revenue change
    if "revenue" in field_lower or "annual_revenue" in field_lower:
        return ChangeType.REVENUE_CHANGE

    # Custom field modification
    if field_name.startswith("Custom_") or field_name.startswith("cf_"):
        return ChangeType.CUSTOM_FIELD_MODIFIED

    # Default to custom field modification
    return ChangeType.CUSTOM_FIELD_MODIFIED


def detect_stalled_deals(
    deals: List[DealRecord],
    threshold_days: int = 30,
) -> List[str]:
    """Detect deals stalled in current stage.

    Algorithm from pseudocode lines 600-608.

    Args:
        deals: List of deal records
        threshold_days: Days threshold for stalled status

    Returns:
        List of stalled deal IDs
    """
    stalled_deal_ids: List[str] = []
    now = datetime.utcnow()

    for deal in deals:
        # Skip closed deals
        if deal.stage in {DealStage.CLOSED_WON, DealStage.CLOSED_LOST}:
            continue

        # Check if stage change date exists
        if not deal.stage_changed_date:
            continue

        # Calculate days in current stage
        days_in_stage = (now - deal.stage_changed_date).days

        if days_in_stage > threshold_days:
            stalled_deal_ids.append(deal.deal_id)
            logger.debug(
                "deal_stalled",
                deal_id=deal.deal_id,
                stage=deal.stage.value,
                days_in_stage=days_in_stage,
            )

    logger.info(
        "stalled_deals_detected",
        total_deals=len(deals),
        stalled_count=len(stalled_deal_ids),
    )

    return stalled_deal_ids


def calculate_inactivity_days(
    last_activity: Optional[datetime],
) -> int:
    """Calculate days since last activity.

    Args:
        last_activity: Last activity timestamp

    Returns:
        Number of days since activity (0 if never)
    """
    if not last_activity:
        return 0

    return (datetime.utcnow() - last_activity).days


def detect_owner_change(
    old_owner_id: str,
    new_owner_id: str,
) -> bool:
    """Detect if account owner changed.

    Args:
        old_owner_id: Previous owner ID
        new_owner_id: Current owner ID

    Returns:
        True if owner changed
    """
    return old_owner_id != new_owner_id


def detect_status_change(
    old_status: str,
    new_status: str,
) -> bool:
    """Detect if account status changed.

    Args:
        old_status: Previous status
        new_status: Current status

    Returns:
        True if status changed
    """
    return old_status != new_status


# ============================================================================
# RISK ASSESSMENT UTILITIES
# ============================================================================

def assess_account_risk(
    account_data: AccountRecord,
    historical_data: Optional[Dict[str, Any]] = None,
) -> RiskLevel:
    """Assess overall account risk level.

    Algorithm from pseudocode lines 1114-1157.

    Args:
        account_data: Current account data
        historical_data: Historical metrics (optional)

    Returns:
        Calculated risk level
    """
    risk_score = 0

    # Inactivity risk (40 points)
    days_inactive = account_data.days_since_activity()
    if days_inactive > 30:
        risk_score += 40
    elif days_inactive > 14:
        risk_score += 20

    # Deal value risk (30 points if low deal value)
    if float(account_data.total_value) == 0:
        risk_score += 30
    elif float(account_data.total_value) < 10000:
        risk_score += 15

    # Status risk (30 points)
    if account_data.status.value == "At Risk":
        risk_score += 30
    elif account_data.status.value == "Inactive":
        risk_score += 25

    # Recent owner change (20 points)
    if account_data.has_change(ChangeType.OWNER_CHANGE):
        risk_score += 20

    # Categorize risk level
    if risk_score >= 80:
        return RiskLevel.CRITICAL
    elif risk_score >= 50:
        return RiskLevel.HIGH
    elif risk_score >= 25:
        return RiskLevel.MEDIUM
    elif risk_score > 0:
        return RiskLevel.LOW
    else:
        return RiskLevel.NONE


def identify_engagement_drop(
    activities: List[ActivityRecord],
    comparison_window_days: int = 30,
) -> bool:
    """Identify significant engagement drop.

    Compares current period to previous period.

    Args:
        activities: List of activity records
        comparison_window_days: Window for comparison

    Returns:
        True if engagement dropped significantly (>50%)
    """
    if not activities:
        return True  # No activities = engagement drop

    now = datetime.utcnow()
    cutoff_current = now - timedelta(days=comparison_window_days)
    cutoff_previous = now - timedelta(days=comparison_window_days * 2)

    # Count activities in each window
    current_count = sum(
        1 for a in activities
        if a.created_time >= cutoff_current
    )

    previous_count = sum(
        1 for a in activities
        if cutoff_previous <= a.created_time < cutoff_current
    )

    # No previous activity = can't determine drop
    if previous_count == 0:
        return False

    # Calculate drop percentage
    drop_percentage = (previous_count - current_count) / previous_count

    logger.debug(
        "engagement_drop_analysis",
        current_count=current_count,
        previous_count=previous_count,
        drop_percentage=drop_percentage,
    )

    return drop_percentage > 0.5  # 50% drop threshold


def generate_risk_signals(
    account: AccountRecord,
    deals: List[DealRecord],
    activities: List[ActivityRecord],
    inactivity_threshold: int = 30,
    deal_stalled_threshold: int = 30,
) -> List[RiskSignal]:
    """Generate risk signals for account.

    Args:
        account: Account record
        deals: Deal records
        activities: Activity records
        inactivity_threshold: Inactivity threshold days
        deal_stalled_threshold: Deal stalled threshold days

    Returns:
        List of identified risk signals
    """
    signals: List[RiskSignal] = []

    # Check inactivity
    days_inactive = account.days_since_activity()
    if days_inactive >= inactivity_threshold:
        signals.append(RiskSignal(
            signal_type="inactivity",
            description=f"No activity in {days_inactive} days",
            severity=RiskLevel.CRITICAL if days_inactive > 60 else RiskLevel.HIGH,
            details={"days_inactive": days_inactive},
            requires_action=True,
        ))

    # Check stalled deals
    stalled_deals = detect_stalled_deals(deals, deal_stalled_threshold)
    if stalled_deals:
        signals.append(RiskSignal(
            signal_type="stalled_deals",
            description=f"{len(stalled_deals)} deal(s) stalled in stage",
            severity=RiskLevel.HIGH,
            details={
                "stalled_deal_ids": stalled_deals,
                "stalled_count": len(stalled_deals),
            },
            requires_action=True,
        ))

    # Check engagement drop
    if identify_engagement_drop(activities):
        signals.append(RiskSignal(
            signal_type="engagement_drop",
            description="Significant decrease in engagement activity",
            severity=RiskLevel.MEDIUM,
            details={"activity_count": len(activities)},
            requires_action=False,
        ))

    # Check owner change
    if account.has_change(ChangeType.OWNER_CHANGE):
        signals.append(RiskSignal(
            signal_type="owner_change",
            description="Account owner recently changed",
            severity=RiskLevel.HIGH,
            details={"change_type": "owner"},
            requires_action=True,
        ))

    # Check status change to At Risk
    if account.status.value == "At Risk":
        signals.append(RiskSignal(
            signal_type="at_risk_status",
            description="Account status marked as At Risk",
            severity=RiskLevel.CRITICAL,
            details={"status": account.status.value},
            requires_action=True,
        ))

    logger.info(
        "risk_signals_generated",
        account_id=account.account_id,
        signal_count=len(signals),
    )

    return signals


# ============================================================================
# DATA AGGREGATION UTILITIES
# ============================================================================

def aggregate_deal_pipeline(
    deals: List[DealRecord],
) -> Dict[str, Any]:
    """Aggregate deal pipeline summary.

    Args:
        deals: List of deal records

    Returns:
        Pipeline summary with stage breakdown
    """
    summary = {
        "total_count": len(deals),
        "total_value": Decimal("0"),
        "weighted_value": Decimal("0"),
        "by_stage": {},
        "stalled_count": 0,
        "avg_probability": 0,
    }

    if not deals:
        return summary

    # Aggregate by stage
    for deal in deals:
        stage = deal.stage.value
        if stage not in summary["by_stage"]:
            summary["by_stage"][stage] = {
                "count": 0,
                "total_value": Decimal("0"),
            }

        summary["by_stage"][stage]["count"] += 1
        summary["by_stage"][stage]["total_value"] += deal.amount
        summary["total_value"] += deal.amount

        # Weighted value (probability-adjusted)
        weighted = deal.amount * Decimal(str(deal.probability / 100))
        summary["weighted_value"] += weighted

        # Count stalled deals
        if deal.is_stalled:
            summary["stalled_count"] += 1

    # Calculate average probability
    if deals:
        summary["avg_probability"] = sum(d.probability for d in deals) / len(deals)

    return summary


def summarize_activities(
    activities: List[ActivityRecord],
    window_days: int = 30,
) -> Dict[str, Any]:
    """Summarize activity patterns.

    Args:
        activities: List of activity records
        window_days: Time window for recent activities

    Returns:
        Activity summary with type breakdown
    """
    cutoff = datetime.utcnow() - timedelta(days=window_days)

    summary = {
        "total_count": len(activities),
        "recent_count": 0,
        "high_value_count": 0,
        "by_type": {},
        "most_recent_date": None,
        "avg_per_month": 0.0,
    }

    if not activities:
        return summary

    # Find most recent activity
    sorted_activities = sorted(activities, key=lambda a: a.created_time, reverse=True)
    summary["most_recent_date"] = sorted_activities[0].created_time

    # Aggregate by type
    for activity in activities:
        activity_type = activity.activity_type.value

        if activity_type not in summary["by_type"]:
            summary["by_type"][activity_type] = 0

        summary["by_type"][activity_type] += 1

        # Count recent activities
        if activity.created_time >= cutoff:
            summary["recent_count"] += 1

        # Count high-value activities
        if activity.is_high_value:
            summary["high_value_count"] += 1

    # Calculate average per month (estimate)
    if activities:
        oldest_activity = min(a.created_time for a in activities)
        months_span = max(1, (datetime.utcnow() - oldest_activity).days / 30)
        summary["avg_per_month"] = len(activities) / months_span

    return summary


def calculate_engagement_score(
    activities: List[ActivityRecord],
    deals: List[DealRecord],
) -> float:
    """Calculate engagement score (0.0 - 1.0).

    Algorithm from pseudocode lines 938-965.

    Factors:
    - Recent activity (40%)
    - Activity frequency (30%)
    - Quality of engagement (30%)

    Args:
        activities: Activity records
        deals: Deal records

    Returns:
        Engagement score 0.0-1.0
    """
    if not activities:
        return 0.0

    score = 0.0

    # Recent activity score (40% weight)
    sorted_activities = sorted(activities, key=lambda a: a.created_time, reverse=True)
    most_recent = sorted_activities[0].created_time
    days_since = (datetime.utcnow() - most_recent).days
    activity_score = max(0.0, 1.0 - (days_since / 30.0))
    score += activity_score * 0.4

    # Activity frequency score (30% weight)
    last_30_days = sum(1 for a in activities if a.is_recent(30))
    frequency_score = min(1.0, last_30_days / 10.0)
    score += frequency_score * 0.3

    # Quality of engagement (30% weight)
    high_value_count = sum(1 for a in activities if a.is_high_value)
    quality_score = min(1.0, high_value_count / 5.0)
    score += quality_score * 0.3

    return min(1.0, score)


def identify_high_value_activities(
    activities: List[ActivityRecord],
    high_value_types: Optional[List[str]] = None,
) -> List[ActivityRecord]:
    """Identify high-value activities.

    Args:
        activities: Activity records
        high_value_types: Activity types considered high-value

    Returns:
        List of high-value activities
    """
    if high_value_types is None:
        high_value_types = [
            ActivityType.DEMO.value,
            ActivityType.CONTRACT_REVIEW.value,
            ActivityType.EXECUTIVE_MEETING.value,
        ]

    return [
        activity for activity in activities
        if activity.activity_type.value in high_value_types
    ]


def calculate_data_freshness(
    last_sync: Optional[datetime],
) -> int:
    """Calculate data freshness in seconds.

    Args:
        last_sync: Last sync timestamp

    Returns:
        Seconds since last sync
    """
    if not last_sync:
        return 0

    return int((datetime.utcnow() - last_sync).total_seconds())


def build_data_summary(
    deals: List[DealRecord],
    activities: List[ActivityRecord],
    notes_count: int,
) -> Dict[str, Any]:
    """Build complete data summary.

    Args:
        deals: Deal records
        activities: Activity records
        notes_count: Number of notes

    Returns:
        Complete data summary
    """
    return {
        "deals": aggregate_deal_pipeline(deals),
        "activities": summarize_activities(activities),
        "notes_count": notes_count,
        "engagement_score": calculate_engagement_score(activities, deals),
        "summary_generated_at": datetime.utcnow().isoformat(),
    }
