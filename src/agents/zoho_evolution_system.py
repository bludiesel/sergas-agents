"""Zoho Agent Evolution System with Continuous Learning.

This system enables Zoho agents to learn from performance metrics, user feedback,
and behavior patterns over time to continuously improve their capabilities.

Key Components:
- LearningType and EvolutionStrategy enums
- PerformanceMetric, FeedbackData, and LearningPattern dataclasses
- PerformanceTracker for metrics collection
- FeedbackProcessor for user feedback analysis
- PatternRecognizer for behavior pattern detection
- EvolutionEngine for driving agent improvements

The system supports multiple learning strategies and provides a framework
for autonomous agent improvement through experience.
"""

import asyncio
import uuid
import json
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


class LearningType(str, Enum):
    """Types of learning mechanisms for agent evolution."""
    REINFORCEMENT = "reinforcement"     # Learning from rewards/penalties
    SUPERVISED = "supervised"          # Learning from labeled examples
    UNSUPERVISED = "unsupervised"      # Learning from unlabeled patterns
    FEDERATED = "federated"            # Learning across multiple agents
    TRANSFER = "transfer"              # Transfer learning from other domains
    HYBRID = "hybrid"                  # Combination of multiple approaches


class EvolutionStrategy(str, Enum):
    """Evolution strategies for agent improvement."""
    GENETIC = "genetic"                # Genetic algorithm-based evolution
    GRADIENT = "gradient"              # Gradient-based optimization
    BAYESIAN = "bayesian"              # Bayesian optimization
    ENSEMBLE = "ensemble"              # Ensemble learning approaches
    META_LEARNING = "meta_learning"    # Learning to learn
    ADAPTIVE = "adaptive"              # Adaptive strategy selection


class MetricType(str, Enum):
    """Types of performance metrics."""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    USER_SATISFACTION = "user_satisfaction"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    RESOURCE_USAGE = "resource_usage"


class FeedbackType(str, Enum):
    """Types of user feedback."""
    EXPLICIT_RATING = "explicit_rating"    # 1-5 star ratings
    THUMBS_UP_DOWN = "thumbs_up_down"      # Binary feedback
    CORRECTION = "correction"              # Explicit corrections
    SUGGESTION = "suggestion"              # Improvement suggestions
    COMPLAINT = "complaint"                # Negative feedback
    COMPLIMENT = "compliment"              # Positive feedback


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""
    metric_id: str = field(default_factory=lambda: f"metric_{uuid.uuid4().hex[:8]}")
    agent_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate metric data."""
        if not 0 <= self.value <= 1 and self.metric_type in [
            MetricType.ACCURACY, MetricType.PRECISION, MetricType.RECALL,
            MetricType.F1_SCORE, MetricType.SUCCESS_RATE, MetricType.USER_SATISFACTION
        ]:
            raise ValueError(f"Metric {self.metric_type} must be between 0 and 1")
        if self.value < 0:
            raise ValueError("Metric values cannot be negative")


@dataclass
class FeedbackData:
    """User feedback data point."""
    feedback_id: str = field(default_factory=lambda: f"feedback_{uuid.uuid4().hex[:8]}")
    agent_id: str
    feedback_type: FeedbackType
    rating: Optional[float] = None          # 1-5 for explicit ratings
    text: Optional[str] = None              # Text feedback
    corrected_response: Optional[str] = None # Corrected output if applicable
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate feedback data."""
        if self.rating is not None and not 1 <= self.rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        if self.feedback_type == FeedbackType.EXPLICIT_RATING and self.rating is None:
            raise ValueError("Explicit rating feedback must include a rating")


@dataclass
class LearningPattern:
    """Discovered learning pattern."""
    pattern_id: str = field(default_factory=lambda: f"pattern_{uuid.uuid4().hex[:8]}")
    agent_id: str
    pattern_type: str
    confidence: float
    frequency: int
    description: str
    conditions: Dict[str, Any] = field(default_factory=dict)
    outcomes: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_observed: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate pattern data."""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Pattern confidence must be between 0 and 1")
        if self.frequency < 1:
            raise ValueError("Pattern frequency must be at least 1")


@dataclass
class EvolutionCheckpoint:
    """Checkpoint capturing agent state at evolution point."""
    checkpoint_id: str = field(default_factory=lambda: f"checkpoint_{uuid.uuid4().hex[:8]}")
    agent_id: str
    generation: int
    performance_summary: Dict[str, float]
    learned_parameters: Dict[str, Any]
    evolution_strategy: EvolutionStrategy
    improvements_made: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceTracker:
    """Tracks and analyzes performance metrics for agents."""

    def __init__(self, max_history_size: int = 10000):
        """Initialize performance tracker.

        Args:
            max_history_size: Maximum number of metrics to keep in history
        """
        self.max_history_size = max_history_size
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        self.agent_summaries: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.logger = logger.bind(component="performance_tracker")

    def record_metric(self, metric: PerformanceMetric) -> None:
        """Record a performance metric.

        Args:
            metric: Performance metric to record
        """
        # Store metric
        self.metrics[metric.agent_id].append(metric)

        # Update agent summary
        self._update_agent_summary(metric.agent_id, metric)

        self.logger.debug(
            "metric_recorded",
            agent_id=metric.agent_id,
            metric_type=metric.metric_type,
            value=metric.value
        )

    def get_agent_performance(self, agent_id: str,
                            metric_types: Optional[List[MetricType]] = None,
                            time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get performance summary for an agent.

        Args:
            agent_id: Agent identifier
            metric_types: Specific metric types to include (optional)
            time_window: Time window for metrics (optional)

        Returns:
            Performance summary dictionary
        """
        agent_metrics = self.metrics.get(agent_id, deque())

        # Filter by time window
        if time_window:
            cutoff_time = datetime.utcnow() - time_window
            agent_metrics = deque(
                [m for m in agent_metrics if m.timestamp >= cutoff_time],
                maxlen=self.max_history_size
            )

        # Filter by metric types
        if metric_types:
            agent_metrics = deque(
                [m for m in agent_metrics if m.metric_type in metric_types],
                maxlen=self.max_history_size
            )

        if not agent_metrics:
            return {"error": "No metrics found for the specified criteria"}

        # Group by metric type
        metrics_by_type = defaultdict(list)
        for metric in agent_metrics:
            metrics_by_type[metric.metric_type].append(metric.value)

        # Calculate statistics
        summary = {
            "agent_id": agent_id,
            "total_metrics": len(agent_metrics),
            "time_range": {
                "start": min(m.timestamp for m in agent_metrics).isoformat(),
                "end": max(m.timestamp for m in agent_metrics).isoformat()
            },
            "metrics": {}
        }

        for metric_type, values in metrics_by_type.items():
            summary["metrics"][metric_type.value] = {
                "count": len(values),
                "latest": values[-1],
                "average": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "trend": self._calculate_trend(values)
            }

        return summary

    def get_top_performers(self, metric_type: MetricType,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing agents for a specific metric.

        Args:
            metric_type: Metric type to rank by
            limit: Maximum number of agents to return

        Returns:
            List of top performers
        """
        agent_scores = {}

        for agent_id, agent_metrics in self.metrics.items():
            # Get latest metrics of specified type
            recent_metrics = [
                m for m in agent_metrics
                if m.metric_type == metric_type and
                m.timestamp >= datetime.utcnow() - timedelta(days=7)
            ]

            if recent_metrics:
                # Use average of recent metrics
                agent_scores[agent_id] = statistics.mean(m.value for m in recent_metrics)

        # Sort and return top performers
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                "agent_id": agent_id,
                "score": score,
                "metric_type": metric_type.value
            }
            for agent_id, score in sorted_agents[:limit]
        ]

    def detect_performance_anomalies(self, agent_id: str,
                                   threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Detect performance anomalies for an agent.

        Args:
            agent_id: Agent identifier
            threshold: Standard deviation threshold for anomaly detection

        Returns:
            List of detected anomalies
        """
        agent_metrics = self.metrics.get(agent_id, deque())
        anomalies = []

        # Group by metric type
        metrics_by_type = defaultdict(list)
        for metric in agent_metrics:
            metrics_by_type[metric.metric_type].append(metric)

        for metric_type, metric_list in metrics_by_type.items():
            if len(metric_list) < 10:  # Need enough data points
                continue

            values = [m.value for m in metric_list]
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values)

            # Find anomalies (values beyond threshold standard deviations)
            for metric in metric_list:
                z_score = abs(metric.value - mean_val) / std_val if std_val > 0 else 0

                if z_score > threshold:
                    anomalies.append({
                        "metric_id": metric.metric_id,
                        "metric_type": metric_type.value,
                        "value": metric.value,
                        "expected_range": [mean_val - threshold * std_val,
                                         mean_val + threshold * std_val],
                        "z_score": z_score,
                        "timestamp": metric.timestamp.isoformat()
                    })

        return anomalies

    def _update_agent_summary(self, agent_id: str, metric: PerformanceMetric) -> None:
        """Update agent performance summary.

        Args:
            agent_id: Agent identifier
            metric: New metric to incorporate
        """
        if agent_id not in self.agent_summaries:
            self.agent_summaries[agent_id] = {
                "first_seen": metric.timestamp,
                "last_updated": metric.timestamp,
                "total_metrics": 0,
                "latest_metrics": {}
            }

        summary = self.agent_summaries[agent_id]
        summary["last_updated"] = metric.timestamp
        summary["total_metrics"] += 1
        summary["latest_metrics"][metric.metric_type.value] = {
            "value": metric.value,
            "timestamp": metric.timestamp.isoformat()
        }

    def _calculate_trend(self, values: List[float], window_size: int = 10) -> str:
        """Calculate trend direction for a series of values.

        Args:
            values: List of metric values
            window_size: Window size for trend calculation

        Returns:
            Trend string: "improving", "declining", or "stable"
        """
        if len(values) < window_size:
            return "insufficient_data"

        # Use last window_size values
        recent_values = values[-window_size:]

        # Calculate linear regression slope
        x = list(range(len(recent_values)))
        y = recent_values

        n = len(recent_values)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

        # Determine trend based on slope magnitude
        if abs(slope) < 0.01:
            return "stable"
        elif slope > 0:
            return "improving"
        else:
            return "declining"


class FeedbackProcessor:
    """Processes and analyzes user feedback for agent improvement."""

    def __init__(self, sentiment_threshold: float = 0.1):
        """Initialize feedback processor.

        Args:
            sentiment_threshold: Threshold for sentiment classification
        """
        self.sentiment_threshold = sentiment_threshold
        self.feedback_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.feedback_patterns: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.logger = logger.bind(component="feedback_processor")

    def process_feedback(self, feedback: FeedbackData) -> Dict[str, Any]:
        """Process user feedback and extract insights.

        Args:
            feedback: Feedback data to process

        Returns:
            Processing results and insights
        """
        # Store feedback
        self.feedback_history[feedback.agent_id].append(feedback)

        # Analyze feedback
        sentiment = self._analyze_sentiment(feedback)
        category = self._categorize_feedback(feedback)
        urgency = self._assess_urgency(feedback)

        # Update patterns
        self._update_feedback_patterns(feedback.agent_id, feedback, sentiment, category)

        result = {
            "feedback_id": feedback.feedback_id,
            "agent_id": feedback.agent_id,
            "sentiment": sentiment,
            "category": category,
            "urgency": urgency,
            "processed_at": datetime.utcnow().isoformat(),
            "insights": self._extract_insights(feedback, sentiment, category)
        }

        self.logger.info(
            "feedback_processed",
            agent_id=feedback.agent_id,
            feedback_type=feedback.feedback_type,
            sentiment=sentiment,
            category=category
        )

        return result

    def get_feedback_summary(self, agent_id: str,
                           time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get feedback summary for an agent.

        Args:
            agent_id: Agent identifier
            time_window: Time window for feedback (optional)

        Returns:
            Feedback summary dictionary
        """
        agent_feedback = self.feedback_history.get(agent_id, deque())

        # Filter by time window
        if time_window:
            cutoff_time = datetime.utcnow() - time_window
            agent_feedback = deque(
                [f for f in agent_feedback if f.timestamp >= cutoff_time],
                maxlen=1000
            )

        if not agent_feedback:
            return {"error": "No feedback found for the specified criteria"}

        # Calculate summary statistics
        total_feedback = len(agent_feedback)
        ratings = [f.rating for f in agent_feedback if f.rating is not None]

        summary = {
            "agent_id": agent_id,
            "total_feedback": total_feedback,
            "time_range": {
                "start": min(f.timestamp for f in agent_feedback).isoformat(),
                "end": max(f.timestamp for f in agent_feedback).isoformat()
            },
            "feedback_types": defaultdict(int),
            "average_rating": statistics.mean(ratings) if ratings else None,
            "rating_distribution": defaultdict(int),
            "sentiment_distribution": defaultdict(int),
            "common_themes": self._identify_common_themes(agent_feedback)
        }

        # Count feedback types and sentiments
        for feedback in agent_feedback:
            summary["feedback_types"][feedback.feedback_type.value] += 1

            sentiment = self._analyze_sentiment(feedback)
            summary["sentiment_distribution"][sentiment] += 1

            if feedback.rating:
                rating_bucket = int(feedback.rating)
                summary["rating_distribution"][rating_bucket] += 1

        return summary

    def get_improvement_suggestions(self, agent_id: str,
                                  min_frequency: int = 3) -> List[Dict[str, Any]]:
        """Get improvement suggestions based on feedback patterns.

        Args:
            agent_id: Agent identifier
            min_frequency: Minimum frequency for pattern consideration

        Returns:
            List of improvement suggestions
        """
        patterns = self.feedback_patterns.get(agent_id, {})
        suggestions = []

        for theme, data in patterns.items():
            if data.get("frequency", 0) >= min_frequency:
                # Generate suggestion based on theme
                suggestion = self._generate_improvement_suggestion(theme, data)
                if suggestion:
                    suggestions.append(suggestion)

        # Sort by priority
        suggestions.sort(key=lambda x: x.get("priority", 0), reverse=True)

        return suggestions

    def _analyze_sentiment(self, feedback: FeedbackData) -> str:
        """Analyze sentiment of feedback.

        Args:
            feedback: Feedback data

        Returns:
            Sentiment classification: "positive", "negative", or "neutral"
        """
        # Use rating if available
        if feedback.rating is not None:
            if feedback.rating >= 4:
                return "positive"
            elif feedback.rating <= 2:
                return "negative"
            else:
                return "neutral"

        # Use feedback type
        positive_types = {FeedbackType.COMPLIMENT, FeedbackType.THUMBS_UP_DOWN}
        negative_types = {FeedbackType.COMPLAINT, FeedbackType.CORRECTION}

        if feedback.feedback_type in positive_types:
            return "positive"
        elif feedback.feedback_type in negative_types:
            return "negative"

        # Use text analysis (simple keyword-based approach)
        if feedback.text:
            positive_words = ["good", "great", "excellent", "helpful", "useful", "thank"]
            negative_words = ["bad", "poor", "wrong", "unhelpful", "confusing", "error"]

            text_lower = feedback.text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)

            if positive_count > negative_count:
                return "positive"
            elif negative_count > positive_count:
                return "negative"

        return "neutral"

    def _categorize_feedback(self, feedback: FeedbackData) -> str:
        """Categorize feedback into improvement areas.

        Args:
            feedback: Feedback data

        Returns:
            Feedback category
        """
        categories = {
            "accuracy": ["wrong", "incorrect", "inaccurate", "error", "mistake"],
            "response_time": ["slow", "delay", "timeout", "quick", "fast"],
            "communication": ["unclear", "confusing", "helpful", "clear", "polite"],
            "functionality": ["feature", "capability", "function", "broken"],
            "user_experience": ["easy", "difficult", "intuitive", "complicated"]
        }

        if feedback.text:
            text_lower = feedback.text.lower()

            # Check each category
            for category, keywords in categories.items():
                if any(keyword in text_lower for keyword in keywords):
                    return category

        # Use feedback type as fallback
        type_mapping = {
            FeedbackType.CORRECTION: "accuracy",
            FeedbackType.SUGGESTION: "functionality",
            FeedbackType.COMPLAINT: "user_experience",
            FeedbackType.COMPLIMENT: "user_experience"
        }

        return type_mapping.get(feedback.feedback_type, "general")

    def _assess_urgency(self, feedback: FeedbackData) -> str:
        """Assess urgency level of feedback.

        Args:
            feedback: Feedback data

        Returns:
            Urgency level: "high", "medium", or "low"
        """
        # High urgency indicators
        high_urgency_words = ["urgent", "critical", "broken", "emergency", "immediately"]
        medium_urgency_words = ["issue", "problem", "concern", "should", "could"]

        if feedback.text:
            text_lower = feedback.text.lower()

            if any(word in text_lower for word in high_urgency_words):
                return "high"
            elif any(word in text_lower for word in medium_urgency_words):
                return "medium"

        # Use rating for urgency
        if feedback.rating is not None:
            if feedback.rating <= 2:
                return "high"
            elif feedback.rating == 3:
                return "medium"

        # Use feedback type
        high_urgency_types = {FeedbackType.COMPLAINT, FeedbackType.CORRECTION}
        medium_urgency_types = {FeedbackType.SUGGESTION}

        if feedback.feedback_type in high_urgency_types:
            return "high"
        elif feedback.feedback_type in medium_urgency_types:
            return "medium"

        return "low"

    def _update_feedback_patterns(self, agent_id: str, feedback: FeedbackData,
                                sentiment: str, category: str) -> None:
        """Update feedback pattern tracking.

        Args:
            agent_id: Agent identifier
            feedback: Feedback data
            sentiment: Analyzed sentiment
            category: Feedback category
        """
        # Extract key themes from text
        themes = self._extract_themes(feedback.text or "")

        for theme in themes:
            if theme not in self.feedback_patterns[agent_id]:
                self.feedback_patterns[agent_id][theme] = {
                    "frequency": 0,
                    "sentiments": defaultdict(int),
                    "categories": defaultdict(int),
                    "first_seen": feedback.timestamp,
                    "last_seen": feedback.timestamp
                }

            pattern = self.feedback_patterns[agent_id][theme]
            pattern["frequency"] += 1
            pattern["sentiments"][sentiment] += 1
            pattern["categories"][category] += 1
            pattern["last_seen"] = feedback.timestamp

    def _extract_themes(self, text: str) -> List[str]:
        """Extract key themes from feedback text.

        Args:
            text: Feedback text

        Returns:
            List of identified themes
        """
        # Simple keyword-based theme extraction
        theme_keywords = {
            "performance": ["slow", "fast", "performance", "speed", "response time"],
            "accuracy": ["wrong", "correct", "accurate", "precision", "error"],
            "usability": ["easy", "difficult", "usability", "interface", "navigation"],
            "features": ["feature", "functionality", "capability", "option"],
            "communication": ["clear", "unclear", "communication", "language", "tone"],
            "reliability": ["reliable", "unstable", "crash", "error", "stable"]
        }

        text_lower = text.lower()
        themes = []

        for theme, keywords in theme_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                themes.append(theme)

        return themes if themes else ["general"]

    def _extract_insights(self, feedback: FeedbackData,
                         sentiment: str, category: str) -> List[str]:
        """Extract insights from feedback.

        Args:
            feedback: Feedback data
            sentiment: Analyzed sentiment
            category: Feedback category

        Returns:
            List of insights
        """
        insights = []

        # Sentiment-based insights
        if sentiment == "negative" and feedback.rating is not None and feedback.rating <= 2:
            insights.append("Strong negative sentiment indicates immediate attention needed")

        # Category-based insights
        if category == "accuracy":
            insights.append("Related to factual correctness or precision")
        elif category == "response_time":
            insights.append("Related to speed and efficiency")
        elif category == "communication":
            insights.append("Related to clarity and interaction style")

        # Text-based insights
        if feedback.text and len(feedback.text) > 100:
            insights.append("Detailed feedback suggests user engagement")

        return insights

    def _identify_common_themes(self, feedback_list: deque) -> List[Dict[str, Any]]:
        """Identify common themes in feedback.

        Args:
            feedback_list: List of feedback items

        Returns:
            List of common themes with frequencies
        """
        theme_counts = defaultdict(int)

        for feedback in feedback_list:
            themes = self._extract_themes(feedback.text or "")
            for theme in themes:
                theme_counts[theme] += 1

        # Sort by frequency and return top themes
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)

        return [
            {"theme": theme, "frequency": count}
            for theme, count in sorted_themes[:5]
        ]

    def _generate_improvement_suggestion(self, theme: str,
                                       pattern_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate improvement suggestion based on feedback pattern.

        Args:
            theme: Feedback theme
            pattern_data: Pattern analysis data

        Returns:
            Improvement suggestion or None
        """
        suggestions = {
            "performance": "Optimize algorithms and caching for better response times",
            "accuracy": "Improve data validation and fact-checking mechanisms",
            "usability": "Enhance user interface and interaction design",
            "features": "Consider adding requested functionality or capabilities",
            "communication": "Refine communication style and clarity",
            "reliability": "Improve error handling and system stability"
        }

        if theme in suggestions:
            # Calculate priority based on frequency and negative sentiment
            frequency = pattern_data["frequency"]
            negative_sentiment = pattern_data["sentiments"].get("negative", 0)
            priority = (frequency * 0.7) + (negative_sentiment * 0.3)

            return {
                "theme": theme,
                "suggestion": suggestions[theme],
                "priority": priority,
                "frequency": frequency,
                "negative_sentiment_ratio": negative_sentiment / frequency,
                "last_updated": pattern_data["last_seen"].isoformat()
            }

        return None


class PatternRecognizer:
    """Recognizes and analyzes behavior patterns in agent performance."""

    def __init__(self, pattern_threshold: float = 0.7):
        """Initialize pattern recognizer.

        Args:
            pattern_threshold: Minimum confidence threshold for pattern recognition
        """
        self.pattern_threshold = pattern_threshold
        self.patterns: Dict[str, List[LearningPattern]] = defaultdict(list)
        self.temporal_patterns: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.logger = logger.bind(component="pattern_recognizer")

    def recognize_patterns(self, agent_id: str,
                          performance_data: List[PerformanceMetric],
                          feedback_data: List[FeedbackData]) -> List[LearningPattern]:
        """Recognize patterns in agent behavior.

        Args:
            agent_id: Agent identifier
            performance_data: List of performance metrics
            feedback_data: List of feedback data

        Returns:
            List of recognized patterns
        """
        recognized_patterns = []

        # Performance patterns
        performance_patterns = self._recognize_performance_patterns(
            agent_id, performance_data
        )
        recognized_patterns.extend(performance_patterns)

        # Feedback patterns
        feedback_patterns = self._recognize_feedback_patterns(
            agent_id, feedback_data
        )
        recognized_patterns.extend(feedback_patterns)

        # Temporal patterns
        temporal_patterns = self._recognize_temporal_patterns(
            agent_id, performance_data, feedback_data
        )
        recognized_patterns.extend(temporal_patterns)

        # Store patterns
        self.patterns[agent_id].extend(recognized_patterns)

        # Limit stored patterns
        if len(self.patterns[agent_id]) > 100:
            self.patterns[agent_id] = self.patterns[agent_id][-100:]

        self.logger.info(
            "patterns_recognized",
            agent_id=agent_id,
            patterns_found=len(recognized_patterns),
            performance_patterns=len(performance_patterns),
            feedback_patterns=len(feedback_patterns),
            temporal_patterns=len(temporal_patterns)
        )

        return recognized_patterns

    def get_agent_patterns(self, agent_id: str,
                          pattern_types: Optional[List[str]] = None) -> List[LearningPattern]:
        """Get patterns for a specific agent.

        Args:
            agent_id: Agent identifier
            pattern_types: Specific pattern types to include (optional)

        Returns:
            List of learning patterns
        """
        agent_patterns = self.patterns.get(agent_id, [])

        if pattern_types:
            agent_patterns = [
                p for p in agent_patterns
                if p.pattern_type in pattern_types
            ]

        return sorted(agent_patterns, key=lambda p: p.confidence, reverse=True)

    def analyze_pattern_evolution(self, agent_id: str,
                                time_window: timedelta = timedelta(days=30)) -> Dict[str, Any]:
        """Analyze how patterns have evolved over time.

        Args:
            agent_id: Agent identifier
            time_window: Time window for analysis

        Returns:
            Pattern evolution analysis
        """
        patterns = self.patterns.get(agent_id, [])
        cutoff_time = datetime.utcnow() - time_window

        # Filter patterns by time window
        recent_patterns = [p for p in patterns if p.discovered_at >= cutoff_time]

        if not recent_patterns:
            return {"error": "No patterns found in the specified time window"}

        # Group patterns by type and time
        patterns_by_type = defaultdict(list)
        for pattern in recent_patterns:
            patterns_by_type[pattern.pattern_type].append(pattern)

        evolution_analysis = {
            "agent_id": agent_id,
            "time_window_days": time_window.days,
            "total_patterns": len(recent_patterns),
            "patterns_by_type": {},
            "trends": {},
            "emerging_patterns": [],
            "declining_patterns": []
        }

        # Analyze each pattern type
        for pattern_type, type_patterns in patterns_by_type.items():
            # Sort by discovery time
            type_patterns.sort(key=lambda p: p.discovered_at)

            evolution_analysis["patterns_by_type"][pattern_type] = {
                "count": len(type_patterns),
                "average_confidence": statistics.mean(p.confidence for p in type_patterns),
                "first_discovered": type_patterns[0].discovered_at.isoformat(),
                "last_discovered": type_patterns[-1].discovered_at.isoformat()
            }

            # Calculate trend (simple linear trend on confidence)
            if len(type_patterns) >= 2:
                confidences = [p.confidence for p in type_patterns]
                trend = self._calculate_simple_trend(confidences)
                evolution_analysis["trends"][pattern_type] = trend

        # Identify emerging and declining patterns
        evolution_analysis["emerging_patterns"] = [
            p.model_dump() for p in recent_patterns
            if p.discovered_at >= datetime.utcnow() - timedelta(days=7)
            and p.confidence >= self.pattern_threshold
        ]

        evolution_analysis["declining_patterns"] = [
            p.model_dump() for p in recent_patterns
            if (datetime.utcnow() - p.last_observed).days > 14
            and p.confidence < self.pattern_threshold
        ]

        return evolution_analysis

    def _recognize_performance_patterns(self, agent_id: str,
                                      metrics: List[PerformanceMetric]) -> List[LearningPattern]:
        """Recognize patterns in performance metrics.

        Args:
            agent_id: Agent identifier
            metrics: Performance metrics

        Returns:
            List of performance patterns
        """
        patterns = []

        # Group metrics by type
        metrics_by_type = defaultdict(list)
        for metric in metrics:
            metrics_by_type[metric.metric_type].append(metric)

        # Analyze each metric type for patterns
        for metric_type, metric_list in metrics_by_type.items():
            if len(metric_list) < 5:  # Need enough data points
                continue

            values = [m.value for m in metric_list]

            # Detect improvement pattern
            if self._is_improvement_trend(values):
                patterns.append(LearningPattern(
                    agent_id=agent_id,
                    pattern_type="performance_improvement",
                    confidence=self._calculate_trend_confidence(values),
                    frequency=len(metric_list),
                    description=f"Consistent improvement in {metric_type.value}",
                    conditions={"metric_type": metric_type.value},
                    outcomes={"trend": "improving", "rate": self._calculate_improvement_rate(values)}
                ))

            # Detect degradation pattern
            elif self._is_degradation_trend(values):
                patterns.append(LearningPattern(
                    agent_id=agent_id,
                    pattern_type="performance_degradation",
                    confidence=self._calculate_trend_confidence(values),
                    frequency=len(metric_list),
                    description=f"Consistent degradation in {metric_type.value}",
                    conditions={"metric_type": metric_type.value},
                    outcomes={"trend": "declining", "rate": self._calculate_degradation_rate(values)}
                ))

            # Detect cyclical pattern
            elif self._is_cyclical_pattern(values):
                patterns.append(LearningPattern(
                    agent_id=agent_id,
                    pattern_type="performance_cyclical",
                    confidence=0.8,
                    frequency=len(metric_list),
                    description=f"Cyclical pattern detected in {metric_type.value}",
                    conditions={"metric_type": metric_type.value},
                    outcomes={"cycle_length": self._estimate_cycle_length(values)}
                ))

        return patterns

    def _recognize_feedback_patterns(self, agent_id: str,
                                   feedback_list: List[FeedbackData]) -> List[LearningPattern]:
        """Recognize patterns in user feedback.

        Args:
            agent_id: Agent identifier
            feedback_list: List of feedback data

        Returns:
            List of feedback patterns
        """
        patterns = []

        if len(feedback_list) < 10:  # Need enough feedback
            return patterns

        # Analyze feedback frequency patterns
        feedback_by_day = defaultdict(int)
        for feedback in feedback_list:
            day_key = feedback.timestamp.date()
            feedback_by_day[day_key] += 1

        # Detect high feedback frequency pattern
        avg_daily_feedback = statistics.mean(feedback_by_day.values())
        if avg_daily_feedback > 5:
            patterns.append(LearningPattern(
                agent_id=agent_id,
                pattern_type="high_feedback_frequency",
                confidence=min(avg_daily_feedback / 10, 1.0),
                frequency=len(feedback_list),
                description="High frequency of user feedback",
                conditions={"avg_daily_feedback": avg_daily_feedback},
                outcomes={"engagement_level": "high", "attention_needed": True}
            ))

        # Analyze sentiment patterns
        sentiment_processor = FeedbackProcessor()
        sentiments = []
        for feedback in feedback_list:
            sentiment = sentiment_processor._analyze_sentiment(feedback)
            sentiments.append(1 if sentiment == "positive" else -1 if sentiment == "negative" else 0)

        # Detect sentiment trend
        if len(sentiments) >= 10 and self._is_improvement_trend(sentiments):
            patterns.append(LearningPattern(
                agent_id=agent_id,
                pattern_type="sentiment_improvement",
                confidence=self._calculate_trend_confidence(sentiments),
                frequency=len(feedback_list),
                description="User sentiment is improving over time",
                conditions={"feedback_count": len(feedback_list)},
                outcomes={"sentiment_trend": "improving"}
            ))

        return patterns

    def _recognize_temporal_patterns(self, agent_id: str,
                                   performance_data: List[PerformanceMetric],
                                   feedback_data: List[FeedbackData]) -> List[LearningPattern]:
        """Recognize temporal patterns in agent behavior.

        Args:
            agent_id: Agent identifier
            performance_data: Performance metrics
            feedback_data: Feedback data

        Returns:
            List of temporal patterns
        """
        patterns = []

        # Time-based performance patterns
        metrics_by_hour = defaultdict(list)
        for metric in performance_data:
            hour = metric.timestamp.hour
            metrics_by_hour[hour].append(metric.value)

        # Check for time-of-day performance patterns
        hour_performance = {}
        for hour, values in metrics_by_hour.items():
            if values:
                hour_performance[hour] = statistics.mean(values)

        if len(hour_performance) >= 3:
            # Find best and worst performing hours
            best_hour = max(hour_performance, key=hour_performance.get)
            worst_hour = min(hour_performance, key=hour_performance.get)

            performance_diff = hour_performance[best_hour] - hour_performance[worst_hour]
            if performance_diff > 0.2:  # Significant difference
                patterns.append(LearningPattern(
                    agent_id=agent_id,
                    pattern_type="temporal_performance_variation",
                    confidence=min(performance_diff * 2, 1.0),
                    frequency=len(hour_performance),
                    description=f"Performance varies by time of day",
                    conditions={"hours_analyzed": len(hour_performance)},
                    outcomes={
                        "best_hour": best_hour,
                        "worst_hour": worst_hour,
                        "performance_difference": performance_diff
                    }
                ))

        return patterns

    def _is_improvement_trend(self, values: List[float]) -> bool:
        """Check if values show an improvement trend.

        Args:
            values: List of numeric values

        Returns:
            True if improvement trend detected
        """
        if len(values) < 3:
            return False

        # Simple linear regression to detect positive trend
        x = list(range(len(values)))
        y = values

        n = len(values)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

        return slope > 0.01  # Positive slope threshold

    def _is_degradation_trend(self, values: List[float]) -> bool:
        """Check if values show a degradation trend.

        Args:
            values: List of numeric values

        Returns:
            True if degradation trend detected
        """
        if len(values) < 3:
            return False

        # Simple linear regression to detect negative trend
        x = list(range(len(values)))
        y = values

        n = len(values)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

        return slope < -0.01  # Negative slope threshold

    def _is_cyclical_pattern(self, values: List[float]) -> bool:
        """Check if values show a cyclical pattern.

        Args:
            values: List of numeric values

        Returns:
            True if cyclical pattern detected
        """
        if len(values) < 6:
            return False

        # Simple autocorrelation-based cycle detection
        def autocorrelation(values, lag):
            n = len(values)
            if n <= lag:
                return 0

            mean_val = statistics.mean(values)
            numerator = sum((values[i] - mean_val) * (values[i + lag] - mean_val)
                          for i in range(n - lag))
            denominator = sum((values[i] - mean_val) ** 2 for i in range(n))

            return numerator / denominator if denominator > 0 else 0

        # Check for significant autocorrelation at different lags
        for lag in range(2, min(len(values) // 2, 10)):
            if abs(autocorrelation(values, lag)) > 0.5:
                return True

        return False

    def _calculate_trend_confidence(self, values: List[float]) -> float:
        """Calculate confidence level for trend detection.

        Args:
            values: List of numeric values

        Returns:
            Confidence level (0-1)
        """
        if len(values) < 3:
            return 0.0

        # Calculate correlation coefficient
        x = list(range(len(values)))
        y = values

        n = len(values)
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(n))

        denominator = (sum_sq_x * sum_sq_y) ** 0.5

        correlation = abs(numerator / denominator) if denominator > 0 else 0

        # Adjust confidence based on data size
        size_factor = min(len(values) / 20, 1.0)

        return correlation * size_factor

    def _calculate_improvement_rate(self, values: List[float]) -> float:
        """Calculate improvement rate per data point.

        Args:
            values: List of numeric values

        Returns:
            Improvement rate
        """
        if len(values) < 2:
            return 0.0

        return (values[-1] - values[0]) / len(values)

    def _calculate_degradation_rate(self, values: List[float]) -> float:
        """Calculate degradation rate per data point.

        Args:
            values: List of numeric values

        Returns:
            Degradation rate (positive value)
        """
        improvement_rate = self._calculate_improvement_rate(values)
        return abs(improvement_rate) if improvement_rate < 0 else 0.0

    def _estimate_cycle_length(self, values: List[float]) -> int:
        """Estimate cycle length in cyclical patterns.

        Args:
            values: List of numeric values

        Returns:
            Estimated cycle length
        """
        if len(values) < 6:
            return 0

        # Find peaks in the data
        peaks = []
        for i in range(1, len(values) - 1):
            if values[i] > values[i-1] and values[i] > values[i+1]:
                peaks.append(i)

        if len(peaks) < 2:
            return 0

        # Calculate average distance between peaks
        distances = [peaks[i+1] - peaks[i] for i in range(len(peaks) - 1)]
        return int(statistics.mean(distances)) if distances else 0

    def _calculate_simple_trend(self, values: List[float]) -> str:
        """Calculate simple trend direction.

        Args:
            values: List of numeric values

        Returns:
            Trend direction: "improving", "declining", or "stable"
        """
        if len(values) < 2:
            return "stable"

        # Compare first and last thirds
        third = len(values) // 3
        if third == 0:
            return "stable"

        first_third = values[:third]
        last_third = values[-third:]

        first_avg = statistics.mean(first_third)
        last_avg = statistics.mean(last_third)

        difference = last_avg - first_avg

        if abs(difference) < 0.05:
            return "stable"
        elif difference > 0:
            return "improving"
        else:
            return "declining"


class EvolutionEngine:
    """Main engine driving agent evolution and continuous learning."""

    def __init__(self, learning_type: LearningType = LearningType.HYBRID,
                 evolution_strategy: EvolutionStrategy = EvolutionStrategy.ADAPTIVE,
                 evolution_interval: timedelta = timedelta(hours=1)):
        """Initialize evolution engine.

        Args:
            learning_type: Primary learning approach
            evolution_strategy: Evolution strategy to use
            evolution_interval: Interval between evolution cycles
        """
        self.learning_type = learning_type
        self.evolution_strategy = evolution_strategy
        self.evolution_interval = evolution_interval

        # Initialize components
        self.performance_tracker = PerformanceTracker()
        self.feedback_processor = FeedbackProcessor()
        self.pattern_recognizer = PatternRecognizer()

        # Evolution state
        self.agent_generations: Dict[str, int] = defaultdict(int)
        self.evolution_checkpoints: Dict[str, List[EvolutionCheckpoint]] = defaultdict(list)
        self.active_evolutions: Dict[str, asyncio.Task] = {}

        # Learning parameters
        self.learning_rates: Dict[str, float] = defaultdict(lambda: 0.1)
        self.adaptation_thresholds: Dict[str, float] = defaultdict(lambda: 0.05)

        self.logger = logger.bind(
            component="evolution_engine",
            learning_type=learning_type,
            evolution_strategy=evolution_strategy
        )

        self.logger.info(
            "evolution_engine_initialized",
            learning_type=learning_type,
            evolution_strategy=evolution_strategy,
            evolution_interval_hours=evolution_interval.total_seconds() / 3600
        )

    async def start_evolution_cycle(self, agent_id: str) -> None:
        """Start continuous evolution cycle for an agent.

        Args:
            agent_id: Agent identifier
        """
        if agent_id in self.active_evolutions:
            self.logger.warning("evolution_already_active", agent_id=agent_id)
            return

        self.logger.info("starting_evolution_cycle", agent_id=agent_id)

        # Create evolution task
        evolution_task = asyncio.create_task(
            self._evolution_loop(agent_id)
        )
        self.active_evolutions[agent_id] = evolution_task

    async def stop_evolution_cycle(self, agent_id: str) -> None:
        """Stop evolution cycle for an agent.

        Args:
            agent_id: Agent identifier
        """
        if agent_id not in self.active_evolutions:
            self.logger.warning("evolution_not_active", agent_id=agent_id)
            return

        # Cancel evolution task
        evolution_task = self.active_evolutions[agent_id]
        evolution_task.cancel()

        try:
            await evolution_task
        except asyncio.CancelledError:
            pass

        del self.active_evolutions[agent_id]

        self.logger.info("evolution_cycle_stopped", agent_id=agent_id)

    async def trigger_evolution(self, agent_id: str,
                              performance_data: Optional[List[PerformanceMetric]] = None,
                              feedback_data: Optional[List[FeedbackData]] = None) -> Dict[str, Any]:
        """Trigger immediate evolution cycle for an agent.

        Args:
            agent_id: Agent identifier
            performance_data: Performance metrics (optional, will fetch if not provided)
            feedback_data: Feedback data (optional, will fetch if not provided)

        Returns:
            Evolution results
        """
        self.logger.info("manual_evolution_triggered", agent_id=agent_id)

        # Get data if not provided
        if performance_data is None:
            performance_data = list(self.performance_tracker.metrics.get(agent_id, []))

        if feedback_data is None:
            feedback_data = list(self.feedback_processor.feedback_history.get(agent_id, []))

        # Perform evolution
        evolution_result = await self._perform_evolution(
            agent_id, performance_data, feedback_data
        )

        return evolution_result

    def record_performance(self, metric: PerformanceMetric) -> None:
        """Record performance metric for evolution tracking.

        Args:
            metric: Performance metric to record
        """
        self.performance_tracker.record_metric(metric)

    def record_feedback(self, feedback: FeedbackData) -> Dict[str, Any]:
        """Record feedback for evolution tracking.

        Args:
            feedback: Feedback data to record

        Returns:
            Processing results
        """
        return self.feedback_processor.process_feedback(feedback)

    def get_evolution_status(self, agent_id: str) -> Dict[str, Any]:
        """Get evolution status for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Evolution status information
        """
        is_active = agent_id in self.active_evolutions
        generation = self.agent_generations.get(agent_id, 0)
        checkpoints = self.evolution_checkpoints.get(agent_id, [])

        # Get latest checkpoint if available
        latest_checkpoint = checkpoints[-1] if checkpoints else None

        # Get current performance summary
        performance_summary = self.performance_tracker.get_agent_performance(agent_id)

        # Get feedback summary
        feedback_summary = self.feedback_processor.get_feedback_summary(agent_id)

        # Get learning patterns
        patterns = self.pattern_recognizer.get_agent_patterns(agent_id)

        return {
            "agent_id": agent_id,
            "evolution_active": is_active,
            "generation": generation,
            "learning_type": self.learning_type.value,
            "evolution_strategy": self.evolution_strategy.value,
            "latest_checkpoint": latest_checkpoint.checkpoint_id if latest_checkpoint else None,
            "total_checkpoints": len(checkpoints),
            "performance_summary": performance_summary,
            "feedback_summary": feedback_summary,
            "learning_patterns": len(patterns),
            "learning_rate": self.learning_rates[agent_id],
            "adaptation_threshold": self.adaptation_thresholds[agent_id]
        }

    async def _evolution_loop(self, agent_id: str) -> None:
        """Main evolution loop for an agent.

        Args:
            agent_id: Agent identifier
        """
        self.logger.info("evolution_loop_started", agent_id=agent_id)

        try:
            while True:
                try:
                    # Get recent data
                    performance_data = list(self.performance_tracker.metrics.get(agent_id, []))
                    feedback_data = list(self.feedback_processor.feedback_history.get(agent_id, []))

                    # Perform evolution
                    await self._perform_evolution(agent_id, performance_data, feedback_data)

                    # Wait for next evolution cycle
                    await asyncio.sleep(self.evolution_interval.total_seconds())

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(
                        "evolution_loop_error",
                        agent_id=agent_id,
                        error=str(e),
                        stack_trace=traceback.format_exc()
                    )
                    # Continue evolution loop despite errors
                    await asyncio.sleep(60)  # Short delay before retry

        except asyncio.CancelledError:
            pass
        finally:
            self.logger.info("evolution_loop_ended", agent_id=agent_id)

    async def _perform_evolution(self, agent_id: str,
                               performance_data: List[PerformanceMetric],
                               feedback_data: List[FeedbackData]) -> Dict[str, Any]:
        """Perform evolution cycle for an agent.

        Args:
            agent_id: Agent identifier
            performance_data: Performance metrics
            feedback_data: Feedback data

        Returns:
            Evolution results
        """
        evolution_start = datetime.utcnow()

        self.logger.info(
            "evolution_cycle_started",
            agent_id=agent_id,
            generation=self.agent_generations[agent_id],
            performance_metrics=len(performance_data),
            feedback_items=len(feedback_data)
        )

        try:
            # Step 1: Recognize patterns
            patterns = self.pattern_recognizer.recognize_patterns(
                agent_id, performance_data, feedback_data
            )

            # Step 2: Analyze performance
            performance_summary = self.performance_tracker.get_agent_performance(agent_id)

            # Step 3: Process feedback
            improvement_suggestions = self.feedback_processor.get_improvement_suggestions(agent_id)

            # Step 4: Determine evolution actions
            evolution_actions = self._determine_evolution_actions(
                agent_id, patterns, performance_summary, improvement_suggestions
            )

            # Step 5: Apply evolution based on strategy
            evolution_results = await self._apply_evolution_strategy(
                agent_id, evolution_actions
            )

            # Step 6: Update agent state
            await self._update_agent_state(agent_id, evolution_results)

            # Step 7: Create checkpoint
            checkpoint = await self._create_evolution_checkpoint(
                agent_id, evolution_results, performance_summary
            )

            evolution_duration = (datetime.utcnow() - evolution_start).total_seconds()

            results = {
                "agent_id": agent_id,
                "generation": self.agent_generations[agent_id],
                "evolution_duration_seconds": evolution_duration,
                "patterns_recognized": len(patterns),
                "evolution_actions": evolution_actions,
                "evolution_results": evolution_results,
                "checkpoint_id": checkpoint.checkpoint_id,
                "performance_summary": performance_summary,
                "improvement_suggestions_count": len(improvement_suggestions)
            }

            self.logger.info(
                "evolution_cycle_completed",
                agent_id=agent_id,
                generation=self.agent_generations[agent_id],
                duration_seconds=evolution_duration,
                patterns_found=len(patterns),
                actions_taken=len(evolution_actions)
            )

            return results

        except Exception as e:
            self.logger.error(
                "evolution_cycle_failed",
                agent_id=agent_id,
                error=str(e),
                stack_trace=traceback.format_exc()
            )
            raise

    def _determine_evolution_actions(self, agent_id: str,
                                   patterns: List[LearningPattern],
                                   performance_summary: Dict[str, Any],
                                   improvement_suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Determine evolution actions based on analysis.

        Args:
            agent_id: Agent identifier
            patterns: Recognized learning patterns
            performance_summary: Performance analysis
            improvement_suggestions: Feedback-based suggestions

        Returns:
            List of evolution actions to take
        """
        actions = []

        # Performance-based actions
        if "metrics" in performance_summary:
            metrics = performance_summary["metrics"]

            # Check for poor performance
            for metric_type, metric_data in metrics.items():
                if metric_data["latest"] < self.adaptation_thresholds[agent_id]:
                    actions.append({
                        "type": "performance_improvement",
                        "priority": "high",
                        "metric_type": metric_type,
                        "current_value": metric_data["latest"],
                        "target_value": self.adaptation_thresholds[agent_id],
                        "action": f"Improve {metric_type} performance"
                    })

        # Pattern-based actions
        for pattern in patterns:
            if pattern.confidence >= self.pattern_recognizer.pattern_threshold:
                if pattern.pattern_type == "performance_degradation":
                    actions.append({
                        "type": "pattern_correction",
                        "priority": "high",
                        "pattern_type": pattern.pattern_type,
                        "confidence": pattern.confidence,
                        "action": "Address performance degradation pattern"
                    })
                elif pattern.pattern_type == "sentiment_improvement":
                    actions.append({
                        "type": "pattern_reinforcement",
                        "priority": "medium",
                        "pattern_type": pattern.pattern_type,
                        "confidence": pattern.confidence,
                        "action": "Reinforce positive sentiment patterns"
                    })

        # Feedback-based actions
        for suggestion in improvement_suggestions:
            if suggestion.get("priority", 0) > 0.7:
                actions.append({
                    "type": "feedback_improvement",
                    "priority": "high",
                    "theme": suggestion["theme"],
                    "frequency": suggestion["frequency"],
                    "action": suggestion["suggestion"]
                })

        # Learning rate adjustment
        if len(patterns) > 5:  # Many patterns detected
            actions.append({
                "type": "learning_rate_adjustment",
                "priority": "medium",
                "current_rate": self.learning_rates[agent_id],
                "new_rate": min(self.learning_rates[agent_id] * 1.2, 0.5),
                "action": "Increase learning rate for faster adaptation"
            })

        return actions

    async def _apply_evolution_strategy(self, agent_id: str,
                                      actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply evolution strategy based on actions.

        Args:
            agent_id: Agent identifier
            actions: Evolution actions to apply

        Returns:
            Evolution application results
        """
        results = {
            "strategy": self.evolution_strategy.value,
            "actions_attempted": len(actions),
            "actions_succeeded": 0,
            "applied_changes": [],
            "errors": []
        }

        for action in actions:
            try:
                if self.evolution_strategy == EvolutionStrategy.ADAPTIVE:
                    change = await self._apply_adaptive_strategy(agent_id, action)
                elif self.evolution_strategy == EvolutionStrategy.GRADIENT:
                    change = await self._apply_gradient_strategy(agent_id, action)
                elif self.evolution_strategy == EvolutionStrategy.BAYESIAN:
                    change = await self._apply_bayesian_strategy(agent_id, action)
                elif self.evolution_strategy == EvolutionStrategy.ENSEMBLE:
                    change = await self._apply_ensemble_strategy(agent_id, action)
                else:
                    change = await self._apply_adaptive_strategy(agent_id, action)

                if change:
                    results["applied_changes"].append(change)
                    results["actions_succeeded"] += 1

            except Exception as e:
                error_msg = f"Failed to apply action {action['type']}: {str(e)}"
                results["errors"].append(error_msg)
                self.logger.error("evolution_action_failed", agent_id=agent_id, action=action, error=str(e))

        return results

    async def _apply_adaptive_strategy(self, agent_id: str,
                                     action: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply adaptive evolution strategy.

        Args:
            agent_id: Agent identifier
            action: Evolution action

        Returns:
            Applied change details
        """
        if action["type"] == "performance_improvement":
            # Adjust learning parameters
            current_rate = self.learning_rates[agent_id]
            adjustment = min(0.1, current_rate * 0.2)
            self.learning_rates[agent_id] = min(current_rate + adjustment, 0.5)

            return {
                "parameter": "learning_rate",
                "old_value": current_rate,
                "new_value": self.learning_rates[agent_id],
                "reason": action["action"]
            }

        elif action["type"] == "learning_rate_adjustment":
            old_rate = self.learning_rates[agent_id]
            self.learning_rates[agent_id] = action["new_rate"]

            return {
                "parameter": "learning_rate",
                "old_value": old_rate,
                "new_value": self.learning_rates[agent_id],
                "reason": action["action"]
            }

        return None

    async def _apply_gradient_strategy(self, agent_id: str,
                                     action: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply gradient-based evolution strategy.

        Args:
            agent_id: Agent identifier
            action: Evolution action

        Returns:
            Applied change details
        """
        # Gradient-based optimization would typically involve
        # calculating gradients and updating weights
        # For this implementation, we'll simulate the effect

        if action["type"] == "performance_improvement":
            # Simulate gradient descent step
            gradient_magnitude = 0.01
            current_rate = self.learning_rates[agent_id]
            self.learning_rates[agent_id] = max(0.01, current_rate - gradient_magnitude)

            return {
                "parameter": "learning_rate",
                "old_value": current_rate,
                "new_value": self.learning_rates[agent_id],
                "reason": f"Gradient descent step for {action['action']}"
            }

        return None

    async def _apply_bayesian_strategy(self, agent_id: str,
                                     action: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply Bayesian evolution strategy.

        Args:
            agent_id: Agent identifier
            action: Evolution action

        Returns:
            Applied change details
        """
        # Bayesian optimization would involve maintaining belief distributions
        # For this implementation, we'll simulate the effect

        if action["type"] == "performance_improvement":
            # Simulate Bayesian update
            current_rate = self.learning_rates[agent_id]
            posterior_mean = (current_rate + 0.2) / 2  # Simple posterior update
            self.learning_rates[agent_id] = posterior_mean

            return {
                "parameter": "learning_rate",
                "old_value": current_rate,
                "new_value": self.learning_rates[agent_id],
                "reason": f"Bayesian update for {action['action']}"
            }

        return None

    async def _apply_ensemble_strategy(self, agent_id: str,
                                     action: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply ensemble evolution strategy.

        Args:
            agent_id: Agent identifier
            action: Evolution action

        Returns:
            Applied change details
        """
        # Ensemble approach combines multiple strategies
        strategies = ["adaptive", "gradient", "bayesian"]
        results = []

        for strategy in strategies:
            if strategy == "adaptive":
                result = await self._apply_adaptive_strategy(agent_id, action)
            elif strategy == "gradient":
                result = await self._apply_gradient_strategy(agent_id, action)
            elif strategy == "bayesian":
                result = await self._apply_bayesian_strategy(agent_id, action)

            if result:
                results.append(result)

        if results:
            # Average the results for ensemble decision
            old_values = [r["old_value"] for r in results if "old_value" in r]
            new_values = [r["new_value"] for r in results if "new_value" in r]

            if old_values and new_values:
                avg_old = statistics.mean(old_values)
                avg_new = statistics.mean(new_values)
                self.learning_rates[agent_id] = avg_new

                return {
                    "parameter": "learning_rate",
                    "old_value": avg_old,
                    "new_value": avg_new,
                    "reason": f"Ensemble decision for {action['action']}",
                    "individual_results": results
                }

        return None

    async def _update_agent_state(self, agent_id: str,
                                 evolution_results: Dict[str, Any]) -> None:
        """Update agent state after evolution.

        Args:
            agent_id: Agent identifier
            evolution_results: Evolution cycle results
        """
        # Increment generation
        self.agent_generations[agent_id] += 1

        # Update adaptation threshold based on performance
        if "performance_summary" in evolution_results:
            performance = evolution_results["performance_summary"]
            if "metrics" in performance:
                avg_performance = statistics.mean([
                    metric_data["latest"]
                    for metric_data in performance["metrics"].values()
                ])

                # Adjust threshold to be slightly above current performance
                self.adaptation_thresholds[agent_id] = min(avg_performance + 0.05, 0.95)

    async def _create_evolution_checkpoint(self, agent_id: str,
                                         evolution_results: Dict[str, Any],
                                         performance_summary: Dict[str, Any]) -> EvolutionCheckpoint:
        """Create evolution checkpoint.

        Args:
            agent_id: Agent identifier
            evolution_results: Evolution cycle results
            performance_summary: Performance summary

        Returns:
            Evolution checkpoint
        """
        checkpoint = EvolutionCheckpoint(
            agent_id=agent_id,
            generation=self.agent_generations[agent_id],
            performance_summary=performance_summary,
            learned_parameters={
                "learning_rate": self.learning_rates[agent_id],
                "adaptation_threshold": self.adaptation_thresholds[agent_id]
            },
            evolution_strategy=self.evolution_strategy,
            improvements_made=evolution_results.get("applied_changes", [])
        )

        # Store checkpoint
        self.evolution_checkpoints[agent_id].append(checkpoint)

        # Limit stored checkpoints
        if len(self.evolution_checkpoints[agent_id]) > 50:
            self.evolution_checkpoints[agent_id] = self.evolution_checkpoints[agent_id][-50:]

        return checkpoint

    def get_evolution_statistics(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get evolution system statistics.

        Args:
            time_window: Time window for statistics (optional)

        Returns:
            Evolution statistics
        """
        total_agents = len(self.agent_generations)
        active_evolutions = len(self.active_evolutions)

        # Calculate total generations and checkpoints
        total_generations = sum(self.agent_generations.values())
        total_checkpoints = sum(len(checkpoints) for checkpoints in self.evolution_checkpoints.values())

        # Performance statistics
        all_performance = []
        for agent_id in self.agent_generations.keys():
            perf_summary = self.performance_tracker.get_agent_performance(agent_id)
            if "metrics" in perf_summary:
                for metric_data in perf_summary["metrics"].values():
                    all_performance.append(metric_data["latest"])

        avg_performance = statistics.mean(all_performance) if all_performance else 0.0

        # Pattern statistics
        total_patterns = sum(len(patterns) for patterns in self.pattern_recognizer.patterns.values())

        statistics = {
            "total_agents": total_agents,
            "active_evolutions": active_evolutions,
            "total_generations": total_generations,
            "total_checkpoints": total_checkpoints,
            "average_performance": avg_performance,
            "total_patterns": total_patterns,
            "learning_type": self.learning_type.value,
            "evolution_strategy": self.evolution_strategy.value,
            "evolution_interval_hours": self.evolution_interval.total_seconds() / 3600
        }

        if time_window:
            # Add time-windowed statistics
            cutoff_time = datetime.utcnow() - time_window

            recent_checkpoints = []
            for checkpoints in self.evolution_checkpoints.values():
                recent_checkpoints.extend([
                    cp for cp in checkpoints if cp.timestamp >= cutoff_time
                ])

            statistics["recent_checkpoints"] = len(recent_checkpoints)
            statistics["recent_generations"] = sum(
                1 for cp in recent_checkpoints
                if cp.timestamp >= cutoff_time
            )

        return statistics


# Export main classes and enums
__all__ = [
    'LearningType',
    'EvolutionStrategy',
    'MetricType',
    'FeedbackType',
    'PerformanceMetric',
    'FeedbackData',
    'LearningPattern',
    'EvolutionCheckpoint',
    'PerformanceTracker',
    'FeedbackProcessor',
    'PatternRecognizer',
    'EvolutionEngine'
]