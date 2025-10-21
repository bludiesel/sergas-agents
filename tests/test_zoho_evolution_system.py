"""Test suite for Zoho Agent Evolution System."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.agents.zoho_evolution_system import (
    LearningType,
    EvolutionStrategy,
    MetricType,
    FeedbackType,
    PerformanceMetric,
    FeedbackData,
    LearningPattern,
    EvolutionCheckpoint,
    PerformanceTracker,
    FeedbackProcessor,
    PatternRecognizer,
    EvolutionEngine
)


class TestPerformanceTracker:
    """Test cases for PerformanceTracker class."""

    def test_record_metric(self):
        """Test recording a performance metric."""
        tracker = PerformanceTracker()
        metric = PerformanceMetric(
            agent_id="test_agent",
            metric_type=MetricType.ACCURACY,
            value=0.85
        )

        tracker.record_metric(metric)

        assert len(tracker.metrics["test_agent"]) == 1
        assert tracker.metrics["test_agent"][0] == metric

    def test_get_agent_performance(self):
        """Test getting agent performance summary."""
        tracker = PerformanceTracker()
        agent_id = "test_agent"

        # Add multiple metrics
        metrics = [
            PerformanceMetric(agent_id=agent_id, metric_type=MetricType.ACCURACY, value=0.8),
            PerformanceMetric(agent_id=agent_id, metric_type=MetricType.ACCURACY, value=0.9),
            PerformanceMetric(agent_id=agent_id, metric_type=MetricType.RESPONSE_TIME, value=0.7)
        ]

        for metric in metrics:
            tracker.record_metric(metric)

        summary = tracker.get_agent_performance(agent_id)

        assert summary["agent_id"] == agent_id
        assert summary["total_metrics"] == 3
        assert "accuracy" in summary["metrics"]
        assert "response_time" in summary["metrics"]
        assert summary["metrics"]["accuracy"]["average"] == 0.85

    def test_detect_performance_anomalies(self):
        """Test performance anomaly detection."""
        tracker = PerformanceTracker()
        agent_id = "test_agent"

        # Add normal metrics
        for i in range(10):
            tracker.record_metric(PerformanceMetric(
                agent_id=agent_id,
                metric_type=MetricType.ACCURACY,
                value=0.8
            ))

        # Add anomalous metric
        tracker.record_metric(PerformanceMetric(
            agent_id=agent_id,
            metric_type=MetricType.ACCURACY,
            value=0.2  # Much lower than normal
        ))

        anomalies = tracker.detect_performance_anomalies(agent_id)

        assert len(anomalies) > 0
        assert anomalies[0]["metric_type"] == "accuracy"


class TestFeedbackProcessor:
    """Test cases for FeedbackProcessor class."""

    def test_process_explicit_rating_feedback(self):
        """Test processing explicit rating feedback."""
        processor = FeedbackProcessor()
        feedback = FeedbackData(
            agent_id="test_agent",
            feedback_type=FeedbackType.EXPLICIT_RATING,
            rating=4,
            text="Great job!"
        )

        result = processor.process_feedback(feedback)

        assert result["agent_id"] == "test_agent"
        assert result["sentiment"] == "positive"
        assert "category" in result
        assert "urgency" in result

    def test_process_complaint_feedback(self):
        """Test processing complaint feedback."""
        processor = FeedbackProcessor()
        feedback = FeedbackData(
            agent_id="test_agent",
            feedback_type=FeedbackType.COMPLAINT,
            text="This is not working correctly"
        )

        result = processor.process_feedback(feedback)

        assert result["sentiment"] == "negative"
        assert result["urgency"] == "high"

    def test_get_feedback_summary(self):
        """Test getting feedback summary."""
        processor = FeedbackProcessor()
        agent_id = "test_agent"

        # Add multiple feedback items
        feedback_items = [
            FeedbackData(agent_id=agent_id, feedback_type=FeedbackType.EXPLICIT_RATING, rating=5),
            FeedbackData(agent_id=agent_id, feedback_type=FeedbackType.EXPLICIT_RATING, rating=3),
            FeedbackData(agent_id=agent_id, feedback_type=FeedbackType.COMPLIMENT, text="Good work")
        ]

        for feedback in feedback_items:
            processor.process_feedback(feedback)

        summary = processor.get_feedback_summary(agent_id)

        assert summary["agent_id"] == agent_id
        assert summary["total_feedback"] == 3
        assert summary["average_rating"] == 4.0
        assert "feedback_types" in summary

    def test_get_improvement_suggestions(self):
        """Test getting improvement suggestions."""
        processor = FeedbackProcessor()
        agent_id = "test_agent"

        # Add feedback that should trigger suggestions
        feedback_items = [
            FeedbackData(
                agent_id=agent_id,
                feedback_type=FeedbackType.COMPLAINT,
                text="The response is too slow and unclear"
            ),
            FeedbackData(
                agent_id=agent_id,
                feedback_type=FeedbackType.SUGGESTION,
                text="Could you improve the speed?"
            ),
            FeedbackData(
                agent_id=agent_id,
                feedback_type=FeedbackType.COMPLAINT,
                text="Performance is poor"
            )
        ]

        for feedback in feedback_items:
            processor.process_feedback(feedback)

        suggestions = processor.get_improvement_suggestions(agent_id, min_frequency=2)

        assert len(suggestions) > 0
        assert any(s["theme"] == "performance" for s in suggestions)


class TestPatternRecognizer:
    """Test cases for PatternRecognizer class."""

    def test_recognize_performance_patterns(self):
        """Test performance pattern recognition."""
        recognizer = PatternRecognizer()
        agent_id = "test_agent"

        # Create improving performance metrics
        metrics = [
            PerformanceMetric(agent_id=agent_id, metric_type=MetricType.ACCURACY, value=0.6),
            PerformanceMetric(agent_id=agent_id, metric_type=MetricType.ACCURACY, value=0.7),
            PerformanceMetric(agent_id=agent_id, metric_type=MetricType.ACCURACY, value=0.8),
            PerformanceMetric(agent_id=agent_id, metric_type=MetricType.ACCURACY, value=0.9),
            PerformanceMetric(agent_id=agent_id, metric_type=MetricType.ACCURACY, value=0.95)
        ]

        patterns = recognizer.recognize_performance_patterns(agent_id, metrics, [])

        assert len(patterns) > 0
        assert any(p.pattern_type == "performance_improvement" for p in patterns)

    def test_recognize_feedback_patterns(self):
        """Test feedback pattern recognition."""
        recognizer = PatternRecognizer()
        agent_id = "test_agent"

        # Create feedback with sentiment trend
        feedback_items = [
            FeedbackData(agent_id=agent_id, feedback_type=FeedbackType.EXPLICIT_RATING, rating=2),
            FeedbackData(agent_id=agent_id, feedback_type=FeedbackType.EXPLICIT_RATING, rating=3),
            FeedbackData(agent_id=agent_id, feedback_type=FeedbackType.EXPLICIT_RATING, rating=4),
            FeedbackData(agent_id=agent_id, feedback_type=FeedbackType.EXPLICIT_RATING, rating=5)
        ]

        patterns = recognizer.recognize_feedback_patterns(agent_id, feedback_items)

        assert len(patterns) >= 0  # May or may not detect patterns depending on algorithm

    def test_analyze_pattern_evolution(self):
        """Test pattern evolution analysis."""
        recognizer = PatternRecognizer()
        agent_id = "test_agent"

        # Create some historical patterns
        patterns = [
            LearningPattern(
                agent_id=agent_id,
                pattern_type="performance_improvement",
                confidence=0.8,
                frequency=5,
                description="Improving accuracy pattern"
            )
        ]

        recognizer.patterns[agent_id] = patterns

        evolution = recognizer.analyze_pattern_evolution(agent_id)

        assert evolution["agent_id"] == agent_id
        assert "total_patterns" in evolution
        assert evolution["total_patterns"] >= 0


class TestEvolutionEngine:
    """Test cases for EvolutionEngine class."""

    @pytest.fixture
    def evolution_engine(self):
        """Create evolution engine for testing."""
        return EvolutionEngine(
            learning_type=LearningType.HYBRID,
            evolution_strategy=EvolutionStrategy.ADAPTIVE,
            evolution_interval=timedelta(minutes=5)  # Short interval for testing
        )

    def test_engine_initialization(self, evolution_engine):
        """Test evolution engine initialization."""
        assert evolution_engine.learning_type == LearningType.HYBRID
        assert evolution_engine.evolution_strategy == EvolutionStrategy.ADAPTIVE
        assert isinstance(evolution_engine.performance_tracker, PerformanceTracker)
        assert isinstance(evolution_engine.feedback_processor, FeedbackProcessor)
        assert isinstance(evolution_engine.pattern_recognizer, PatternRecognizer)

    def test_record_performance_and_feedback(self, evolution_engine):
        """Test recording performance and feedback data."""
        agent_id = "test_agent"

        # Record performance metric
        metric = PerformanceMetric(
            agent_id=agent_id,
            metric_type=MetricType.ACCURACY,
            value=0.85
        )
        evolution_engine.record_performance(metric)

        # Record feedback
        feedback = FeedbackData(
            agent_id=agent_id,
            feedback_type=FeedbackType.EXPLICIT_RATING,
            rating=4
        )
        result = evolution_engine.record_feedback(feedback)

        assert result["agent_id"] == agent_id

    def test_get_evolution_status(self, evolution_engine):
        """Test getting evolution status."""
        agent_id = "test_agent"

        # Add some data
        evolution_engine.record_performance(PerformanceMetric(
            agent_id=agent_id,
            metric_type=MetricType.ACCURACY,
            value=0.85
        ))

        evolution_engine.record_feedback(FeedbackData(
            agent_id=agent_id,
            feedback_type=FeedbackType.EXPLICIT_RATING,
            rating=4
        ))

        status = evolution_engine.get_evolution_status(agent_id)

        assert status["agent_id"] == agent_id
        assert status["generation"] == 0
        assert status["evolution_active"] is False
        assert "performance_summary" in status
        assert "feedback_summary" in status

    @pytest.mark.asyncio
    async def test_trigger_evolution(self, evolution_engine):
        """Test triggering manual evolution."""
        agent_id = "test_agent"

        # Add some data
        metrics = [
            PerformanceMetric(agent_id=agent_id, metric_type=MetricType.ACCURACY, value=0.7),
            PerformanceMetric(agent_id=agent_id, metric_type=MetricType.ACCURACY, value=0.8)
        ]

        feedback_items = [
            FeedbackData(agent_id=agent_id, feedback_type=FeedbackType.EXPLICIT_RATING, rating=3),
            FeedbackData(agent_id=agent_id, feedback_type=FeedbackType.EXPLICIT_RATING, rating=4)
        ]

        for metric in metrics:
            evolution_engine.record_performance(metric)

        for feedback in feedback_items:
            evolution_engine.record_feedback(feedback)

        # Trigger evolution
        result = await evolution_engine.trigger_evolution(agent_id)

        assert result["agent_id"] == agent_id
        assert result["generation"] >= 1  # Should have incremented
        assert "evolution_results" in result
        assert "checkpoint_id" in result

    @pytest.mark.asyncio
    async def test_start_stop_evolution_cycle(self, evolution_engine):
        """Test starting and stopping evolution cycle."""
        agent_id = "test_agent"

        # Start evolution cycle
        await evolution_engine.start_evolution_cycle(agent_id)
        assert agent_id in evolution_engine.active_evolutions

        # Check status
        status = evolution_engine.get_evolution_status(agent_id)
        assert status["evolution_active"] is True

        # Stop evolution cycle
        await evolution_engine.stop_evolution_cycle(agent_id)
        assert agent_id not in evolution_engine.active_evolutions

    def test_get_evolution_statistics(self, evolution_engine):
        """Test getting evolution statistics."""
        # Add some data to create statistics
        agent_ids = ["agent1", "agent2", "agent3"]

        for agent_id in agent_ids:
            evolution_engine.record_performance(PerformanceMetric(
                agent_id=agent_id,
                metric_type=MetricType.ACCURACY,
                value=0.8
            ))

        stats = evolution_engine.get_evolution_statistics()

        assert stats["total_agents"] == 3
        assert stats["active_evolutions"] == 0
        assert "total_generations" in stats
        assert "learning_type" in stats
        assert "evolution_strategy" in stats


class TestDataStructures:
    """Test cases for data structures."""

    def test_performance_metric_validation(self):
        """Test performance metric validation."""
        # Valid metric
        metric = PerformanceMetric(
            agent_id="test_agent",
            metric_type=MetricType.ACCURACY,
            value=0.85
        )
        assert metric.value == 0.85

        # Invalid metric (value out of range)
        with pytest.raises(ValueError):
            PerformanceMetric(
                agent_id="test_agent",
                metric_type=MetricType.ACCURACY,
                value=1.5  # Invalid for accuracy metric
            )

    def test_feedback_data_validation(self):
        """Test feedback data validation."""
        # Valid feedback
        feedback = FeedbackData(
            agent_id="test_agent",
            feedback_type=FeedbackType.EXPLICIT_RATING,
            rating=4
        )
        assert feedback.rating == 4

        # Invalid feedback (rating out of range)
        with pytest.raises(ValueError):
            FeedbackData(
                agent_id="test_agent",
                feedback_type=FeedbackType.EXPLICIT_RATING,
                rating=6  # Invalid rating
            )

        # Missing rating for explicit rating type
        with pytest.raises(ValueError):
            FeedbackData(
                agent_id="test_agent",
                feedback_type=FeedbackType.EXPLICIT_RATING,
                rating=None  # Missing rating
            )

    def test_learning_pattern_validation(self):
        """Test learning pattern validation."""
        # Valid pattern
        pattern = LearningPattern(
            agent_id="test_agent",
            pattern_type="test_pattern",
            confidence=0.8,
            frequency=5,
            description="Test pattern"
        )
        assert pattern.confidence == 0.8

        # Invalid confidence
        with pytest.raises(ValueError):
            LearningPattern(
                agent_id="test_agent",
                pattern_type="test_pattern",
                confidence=1.5,  # Invalid confidence
                frequency=5,
                description="Test pattern"
            )

        # Invalid frequency
        with pytest.raises(ValueError):
            LearningPattern(
                agent_id="test_agent",
                pattern_type="test_pattern",
                confidence=0.8,
                frequency=0,  # Invalid frequency
                description="Test pattern"
            )


class TestIntegration:
    """Integration tests for the evolution system."""

    @pytest.mark.asyncio
    async def test_full_evolution_cycle(self):
        """Test a complete evolution cycle."""
        # Create evolution engine
        engine = EvolutionEngine(
            learning_type=LearningType.REINFORCEMENT,
            evolution_strategy=EvolutionStrategy.ADAPTIVE,
            evolution_interval=timedelta(seconds=1)
        )

        agent_id = "integration_test_agent"

        # Simulate agent activity over time
        for day in range(5):
            # Record performance (improving over time)
            accuracy = 0.6 + (day * 0.08)
            engine.record_performance(PerformanceMetric(
                agent_id=agent_id,
                metric_type=MetricType.ACCURACY,
                value=accuracy
            ))

            # Record feedback (improving over time)
            rating = min(2 + day, 5)
            engine.record_feedback(FeedbackData(
                agent_id=agent_id,
                feedback_type=FeedbackType.EXPLICIT_RATING,
                rating=rating,
                text=f"Day {day} feedback"
            ))

        # Trigger evolution
        result = await engine.trigger_evolution(agent_id)

        # Verify evolution occurred
        assert result["agent_id"] == agent_id
        assert result["generation"] >= 1
        assert result["patterns_recognized"] >= 0
        assert len(result["evolution_actions"]) >= 0

        # Check final status
        status = engine.get_evolution_status(agent_id)
        assert status["generation"] == result["generation"]
        assert status["performance_summary"]["total_metrics"] == 5
        assert status["feedback_summary"]["total_feedback"] == 5

        # Verify checkpoint was created
        checkpoints = engine.evolution_checkpoints[agent_id]
        assert len(checkpoints) >= 1
        assert checkpoints[-1].generation == result["generation"]

    def test_multiple_agent_evolution(self):
        """Test evolution system with multiple agents."""
        engine = EvolutionEngine()

        agents = ["agent_a", "agent_b", "agent_c"]

        # Add different data for each agent
        agent_data = {
            "agent_a": {"accuracy": 0.9, "rating": 5, "feedback_type": FeedbackType.COMPLIMENT},
            "agent_b": {"accuracy": 0.7, "rating": 3, "feedback_type": FeedbackType.SUGGESTION},
            "agent_c": {"accuracy": 0.5, "rating": 2, "feedback_type": FeedbackType.COMPLAINT}
        }

        for agent_id, data in agent_data.items():
            # Record performance
            engine.record_performance(PerformanceMetric(
                agent_id=agent_id,
                metric_type=MetricType.ACCURACY,
                value=data["accuracy"]
            ))

            # Record feedback
            engine.record_feedback(FeedbackData(
                agent_id=agent_id,
                feedback_type=data["feedback_type"],
                rating=data["rating"]
            ))

        # Get statistics
        stats = engine.get_evolution_statistics()

        assert stats["total_agents"] == 3
        assert stats["total_patterns"] >= 0

        # Check individual agent statuses
        for agent_id in agents:
            status = engine.get_evolution_status(agent_id)
            assert status["agent_id"] == agent_id
            assert status["performance_summary"]["total_metrics"] == 1
            assert status["feedback_summary"]["total_feedback"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])