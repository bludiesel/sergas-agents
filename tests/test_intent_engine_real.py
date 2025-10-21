"""Real IntentDetectionEngine Test Suite.

Tests the actual IntentDetectionEngine implementation with comprehensive coverage
of all intent detection capabilities, routing decisions, and edge cases.
"""

import pytest
import asyncio
import time
from datetime import datetime
from src.agents.intent_detection import (
    IntentDetectionEngine,
    IntentCategory,
    ConfidenceLevel,
    IntentResult,
    KeywordPatterns
)


class TestIntentDetectionEngine:
    """Comprehensive test suite for IntentDetectionEngine."""

    @pytest.fixture
    def engine(self):
        """Create intent detection engine for testing."""
        return IntentDetectionEngine(confidence_threshold=0.5)

    @pytest.fixture
    def high_threshold_engine(self):
        """Create engine with high confidence threshold."""
        return IntentDetectionEngine(confidence_threshold=0.8)

    @pytest.fixture
    def low_threshold_engine(self):
        """Create engine with low confidence threshold."""
        return IntentDetectionEngine(confidence_threshold=0.3)


class TestAccountAnalysisIntent(TestIntentDetectionEngine):
    """Test account analysis intent detection."""

    @pytest.mark.parametrize("message,expected_min_confidence", [
        ("Analyze account ACC-12345 for risk factors", 0.8),
        ("Review customer health status", 0.6),
        ("Check account performance metrics", 0.6),
        ("Evaluate client retention risks", 0.6),
        ("Assess account engagement patterns", 0.5),
        ("Monitor account risk indicators", 0.7),
        ("Examine account performance data", 0.6),
        ("Investigate customer account issues", 0.6)
    ])
    def test_account_analysis_keywords(self, engine, message, expected_min_confidence):
        """Test account analysis keyword detection."""
        result = engine.analyze_intent(message)

        assert result.primary_intent == IntentCategory.ACCOUNT_ANALYSIS
        assert result.confidence_score >= expected_min_confidence
        assert result.requires_account_data == True
        assert result.should_call_zoho_agent == True
        assert len(result.keywords_matched) > 0

    def test_account_id_patterns(self, engine):
        """Test various account ID pattern recognition."""
        test_cases = [
            ("Analyze Account-12345", "Account-12345"),
            ("Check ACC-67890", "ACC-67890"),
            ("Review Client-ABC123", "Client-ABC123"),
            ("Evaluate Customer-XYZ789", "Customer-XYZ789"),
            ("Assess #12345", "#12345"),
            ("Monitor account-abcdef", "account-abcdef")
        ]

        for message, expected_account_id in test_cases:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.ACCOUNT_ANALYSIS
            assert result.confidence_score >= 0.8
            assert any(expected_account_id.lower() in pattern.lower() for pattern in result.patterns_matched)

    def test_risk_analysis_detection(self, engine):
        """Test risk analysis keyword detection."""
        risk_messages = [
            "What are the risk indicators for this account?",
            "Identify potential risks in customer data",
            "Assess risk factors for account performance",
            "Risk assessment needed for client portfolio",
            "Monitor risk levels in account health"
        ]

        for message in risk_messages:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.ACCOUNT_ANALYSIS
            assert result.confidence_score >= 0.6
            assert "risk" in [kw.lower() for kw in result.keywords_matched]

    def test_multiple_account_signals(self, engine):
        """Test detection with multiple account signals."""
        message = "Please review account ACC-789 for customer retention risks and analyze engagement metrics"
        result = engine.analyze_intent(message)

        assert result.primary_intent == IntentCategory.ACCOUNT_ANALYSIS
        assert result.confidence_score >= 0.8
        assert len(result.keywords_matched) >= 4
        assert result.requires_account_data == True
        assert result.should_call_zoho_agent == True

    def test_account_with_memory_context(self, engine):
        """Test account analysis with historical context request."""
        message = "Show historical trends for account ACC-456 performance over last quarter"
        result = engine.analyze_intent(message)

        assert result.primary_intent == IntentCategory.ACCOUNT_ANALYSIS
        assert result.should_call_memory_agent == True
        assert result.should_call_zoho_agent == True
        assert result.requires_account_data == True


class TestZohoSpecificIntent(TestIntentDetectionEngine):
    """Test Zoho-specific intent detection."""

    def test_explicit_zoho_mentions(self, engine):
        """Test explicit Zoho CRM mentions."""
        zoho_messages = [
            "Connect to Zoho CRM to get account data",
            "Import records from Zoho",
            "Sync with Zoho database",
            "Export data to Zoho CRM",
            "Zoho integration setup needed"
        ]

        for message in zoho_messages:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.ZOHO_SPECIFIC
            assert result.confidence_score >= 0.7
            assert result.should_call_zoho_agent == True
            assert "zoho" in [kw.lower() for kw in result.keywords_matched]

    def test_crm_general_terms(self, engine):
        """Test general CRM terminology."""
        crm_messages = [
            "Connect to customer relationship management system",
            "Import data from CRM platform",
            "Sync with salesforce database",
            "Hubspot integration required",
            "CRM data migration project"
        ]

        for message in crm_messages:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.ZOHO_SPECIFIC
            assert result.should_call_zoho_agent == True

    def test_zoho_modules_and_data(self, engine):
        """Test Zoho module-specific requests."""
        module_messages = [
            "Get deals and contacts from Zoho modules",
            "Import leads from Zoho CRM",
            "Export account data from Zoho",
            "Sync activities with Zoho system",
            "Retrieve custom fields from Zoho"
        ]

        for message in module_messages:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.ZOHO_SPECIFIC
            assert len(result.keywords_matched) >= 2

    def test_zoho_with_account_context(self, engine):
        """Test Zoho requests with specific account context."""
        message = "Use Zoho CRM to analyze account ACC-123 data"
        result = engine.analyze_intent(message)

        assert result.primary_intent == IntentCategory.ZOHO_SPECIFIC
        assert result.should_call_zoho_agent == True
        assert result.requires_account_data == True
        assert result.confidence_score >= 0.8


class TestMemoryHistoryIntent(TestIntentDetectionEngine):
    """Test memory and history intent detection."""

    @pytest.mark.parametrize("message,expected_min_confidence", [
        ("Show historical trends for customer data", 0.6),
        ("What patterns do we see in past performance?", 0.6),
        ("Compare current vs previous quarter results", 0.6),
        ("Analyze historical account changes", 0.6),
        ("Display timeline of account activities", 0.5),
        ("Show evolution of customer relationship", 0.5),
        ("Historical analysis of sales patterns", 0.6),
        "Track account changes over time", 0.5
    ])
    def test_historical_keywords(self, engine, message, expected_min_confidence):
        """Test historical data keyword detection."""
        result = engine.analyze_intent(message)

        assert result.primary_intent == IntentCategory.MEMORY_HISTORY
        assert result.confidence_score >= expected_min_confidence
        assert result.should_call_memory_agent == True

    def test_timeline_and_period_analysis(self, engine):
        """Test timeline and period analysis requests."""
        period_messages = [
            "Show account evolution over the last 6 months",
            "Analyze quarterly performance trends",
            "Monthly account activity summary",
            "Year-over-year comparison needed",
            "Track weekly engagement patterns"
        ]

        for message in period_messages:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.MEMORY_HISTORY
            assert result.should_call_memory_agent == True
            assert any(period in result.keywords_matched for period in ["months", "quarterly", "monthly", "year", "weekly"])

    def test_pattern_recognition(self, engine):
        """Test pattern recognition requests."""
        pattern_messages = [
            "What patterns emerge from customer engagement data?",
            "Identify trends in account performance",
            "Detect recurring issues in client interactions",
            "Find patterns in sales cycle duration",
            "Analyze behavioral patterns from account data"
        ]

        for message in pattern_messages:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.MEMORY_HISTORY
            assert "patterns" in result.keywords_matched or "trends" in result.keywords_matched

    def test_comparison_analysis(self, engine):
        """Test comparison and trend analysis."""
        comparison_messages = [
            "Compare performance trends between accounts",
            "Benchmark against historical data",
            "Contrast current vs past account status",
            "Relative performance analysis needed",
            "Comparative study of account metrics"
        ]

        for message in comparison_messages:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.MEMORY_HISTORY
            assert result.should_call_memory_agent == True


class TestGeneralConversationIntent(TestIntentDetectionEngine):
    """Test general conversation intent detection."""

    def test_greeting_messages(self, engine):
        """Test greeting and general conversation starters."""
        greetings = [
            "Hello, how are you?",
            "Hi there!",
            "Good morning",
            "Good afternoon",
            "Greetings",
            "Hey",
            "Hiya",
            "Thank you for your help",
            "Thanks",
            "Appreciate your assistance"
        ]

        for message in greetings:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.GENERAL_CONVERSATION
            assert result.confidence_score >= 0.3
            assert result.requires_account_data == False
            assert result.should_call_zoho_agent == False
            assert result.should_call_memory_agent == False

    def test_help_requests(self, engine):
        """Test help and assistance requests."""
        help_messages = [
            "How can you help me?",
            "What can you do?",
            "Can you explain the features?",
            "I need assistance with account analysis",
            "Help me understand the dashboard",
            "What capabilities do you have?",
            "Can you guide me through this?",
            "I need some help here"
        ]

        for message in help_messages:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.HELP_ASSISTANCE
            assert result.requires_account_data == False

    def test_general_questions(self, engine):
        """Test general questions without account specificity."""
        questions = [
            "What are best practices for customer retention?",
            "How do I improve sales performance?",
            "Can you explain risk assessment methodologies?",
            "What metrics should I track for business growth?",
            "How does account analysis work?",
            "What's involved in customer relationship management?"
        ]

        for message in questions:
            result = engine.analyze_intent(message)
            assert result.primary_intent in [IntentCategory.HELP_ASSISTANCE, IntentCategory.GENERAL_CONVERSATION]
            assert result.requires_account_data == False

    def test_short_and_ambiguous_messages(self, engine):
        """Test handling of short, ambiguous messages."""
        short_messages = [
            "help",
            "hello",
            "thanks",
            "ok",
            "hi",
            "yes",
            "no",
            "maybe"
        ]

        for message in short_messages:
            result = engine.analyze_intent(message)
            assert result.confidence_score <= 0.6
            assert result.primary_intent in [IntentCategory.GENERAL_CONVERSATION, IntentCategory.HELP_ASSISTANCE]
            assert result.requires_account_data == False


class TestConfidenceScoring(TestIntentDetectionEngine):
    """Test confidence scoring accuracy and levels."""

    def test_very_high_confidence_patterns(self, engine):
        """Test very high confidence for clear pattern matches."""
        clear_messages = [
            "review account ACC-XYZ789 for risk factors",
            "analyze Account-12345 performance metrics",
            "Check Customer-ABC678 for retention issues"
        ]

        for message in clear_messages:
            result = engine.analyze_intent(message)
            assert result.confidence_score >= 0.9
            assert result.confidence_level == ConfidenceLevel.VERY_HIGH
            assert result.primary_intent == IntentCategory.ACCOUNT_ANALYSIS

    def test_high_confidence_requests(self, engine):
        """Test high confidence for specific requests."""
        specific_messages = [
            "Analyze account ACC-123 for customer retention risks and performance metrics",
            "Show me Zoho CRM data for account ACC-456",
            "Get historical trends for account ACC-789 performance"
        ]

        for message in specific_messages:
            result = engine.analyze_intent(message)
            assert result.confidence_score >= 0.8
            assert result.confidence_level == ConfidenceLevel.HIGH

    def test_medium_confidence_requests(self, engine):
        """Test medium confidence for moderately specific requests."""
        moderate_messages = [
            "Check on customer status",
            "Review account performance",
            "Show client data",
            "Analyze business metrics"
        ]

        for message in moderate_messages:
            result = engine.analyze_intent(message)
            assert 0.5 <= result.confidence_score < 0.8
            assert result.confidence_level == ConfidenceLevel.MEDIUM

    def test_low_confidence_ambiguous(self, engine):
        """Test low confidence for ambiguous messages."""
        ambiguous_messages = [
            "tell me more",
            "show me something",
            "what's next",
            "help with stuff",
            "do something"
        ]

        for message in ambiguous_messages:
            result = engine.analyze_intent(message)
            assert result.confidence_score < 0.5
            assert result.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]

    def test_confidence_threshold_filtering(self, high_threshold_engine):
        """Test confidence threshold filtering effects."""
        medium_confidence_message = "Check on customer status"
        result = high_threshold_engine.analyze_intent(medium_confidence_message)

        # With high threshold, this should not trigger specialized routing
        assert result.requires_account_data == False
        assert result.should_call_zoho_agent == False


class TestRoutingDecisions(TestIntentDetectionEngine):
    """Test routing decision logic and methods."""

    def test_account_analysis_routing(self, engine):
        """Test routing decisions for account analysis."""
        message = "Analyze account ACC-123 for risks"
        result = engine.analyze_intent(message)

        assert engine.requires_account_data(result) == True
        assert engine.should_call_zoho_agent(result) == True
        assert engine.should_call_memory_agent(result) == False

    def test_memory_analysis_routing(self, engine):
        """Test routing decisions for memory analysis."""
        message = "Show historical trends for account performance"
        result = engine.analyze_intent(message)

        assert engine.should_call_memory_agent(result) == True
        # May or may not require account data depending on specificity

    def test_general_conversation_routing(self, engine):
        """Test routing decisions for general conversation."""
        message = "Hello, how can you help me today?"
        result = engine.analyze_intent(message)

        assert engine.requires_account_data(result) == False
        assert engine.should_call_zoho_agent(result) == False
        assert engine.should_call_memory_agent(result) == False

    def test_zoho_integration_routing(self, engine):
        """Test routing decisions for Zoho integration."""
        message = "Connect to Zoho CRM to import account data"
        result = engine.analyze_intent(message)

        assert engine.should_call_zoho_agent(result) == True

    def test_combined_intent_routing(self, engine):
        """Test routing for combined intents requiring multiple agents."""
        message = "Show historical Zoho CRM data for account ACC-456 trends"
        result = engine.analyze_intent(message)

        # Should trigger multiple agents
        assert engine.should_call_zoho_agent(result) == True
        assert engine.should_call_memory_agent(result) == True
        assert engine.requires_account_data(result) == True

    def test_threshold_based_routing(self, high_threshold_engine, low_threshold_engine):
        """Test routing differences with different confidence thresholds."""
        message = "Check customer status"  # Medium confidence message

        high_result = high_threshold_engine.analyze_intent(message)
        low_result = low_threshold_engine.analyze_intent(message)

        # Low threshold engine should be more permissive
        assert low_result.requires_account_data == True
        assert high_result.requires_account_data == False


class TestPatternMatching(TestIntentDetectionEngine):
    """Test regex pattern matching capabilities."""

    def test_account_id_regex_patterns(self, engine):
        """Test various account ID regex patterns."""
        account_formats = [
            "Account-12345",
            "ACC-67890",
            "Client-ABC123",
            "Customer-XYZ789",
            "#12345",
            "account-abcdef",
            "ACC-123-XYZ"  # Complex format
        ]

        for account_id in account_formats:
            message = f"Analyze {account_id} for risks"
            result = engine.analyze_intent(message)

            assert result.primary_intent == IntentCategory.ACCOUNT_ANALYSIS
            assert result.confidence_score >= 0.8
            assert len(result.patterns_matched) > 0

    def test_review_pattern_matching(self, engine):
        """Test account review pattern matching."""
        review_patterns = [
            "review account performance",
            "analyze customer health",
            "check client status",
            "evaluate account metrics",
            "assess business performance"
        ]

        for message in review_patterns:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.ACCOUNT_ANALYSIS
            assert len(result.patterns_matched) > 0

    def test_historical_pattern_matching(self, engine):
        """Test historical analysis pattern matching."""
        historical_patterns = [
            "history of performance data",
            "historical trends in customer engagement",
            "past performance patterns",
            "previous quarter results analysis",
            "timeline of account changes"
        ]

        for message in historical_patterns:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.MEMORY_HISTORY
            assert len(result.patterns_matched) > 0

    def test_help_pattern_matching(self, engine):
        """Test help request pattern matching."""
        help_patterns = [
            "help me understand account analysis",
            "can you assist with customer data?",
            "need guidance on risk assessment",
            "how do I improve retention rates?"
        ]

        for message in help_patterns:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.HELP_ASSISTANCE
            assert len(result.patterns_matched) > 0


class TestEdgeCasesAndErrorHandling(TestIntentDetectionEngine):
    """Test edge cases and error handling."""

    def test_empty_message_handling(self, engine):
        """Test handling of empty and whitespace messages."""
        empty_inputs = ["", "   ", "\t", "\n", "   \t\n   "]

        for empty_input in empty_inputs:
            result = engine.analyze_intent(empty_input)
            assert result.primary_intent == IntentCategory.UNKNOWN
            assert result.confidence_score == 0.0
            assert result.requires_account_data == False
            assert result.message_length == len(empty_input)

    def test_extremely_long_messages(self, engine):
        """Test handling of very long messages."""
        long_message = "analyze " + "account " * 1000 + "ACC-123 " + "performance metrics " * 500
        result = engine.analyze_intent(long_message)

        assert result.primary_intent == IntentCategory.ACCOUNT_ANALYSIS
        assert result.confidence_score > 0.5
        assert result.message_length == len(long_message)
        assert result.processing_time_ms < 1000  # Should complete within 1 second

    def test_special_characters_and_unicode(self, engine):
        """Test handling of special characters and unicode."""
        special_messages = [
            "Analyze account ACC-123@#$%^&*() for risks!",
            "Héllo, hów are yøu? 🌟",
            "Analyze account ÁÇÇ-123 with special chars: @#$%",
            "Show me data for acc-测试 (Chinese test)",
            "مرحبا، أحتاج مساعدة (Arabic help request)",
            "Привет, проанализируй счет ACC-456 (Russian)"
        ]

        for message in special_messages:
            result = engine.analyze_intent(message)
            assert result is not None
            assert isinstance(result.confidence_score, float)
            assert 0.0 <= result.confidence_score <= 1.0

    def test_mixed_case_handling(self, engine):
        """Test case-insensitive matching."""
        case_variations = [
            "ANALYZE Account ACC-123",
            "analyze account acc-123",
            "Analyze ACCOUNT Acc-123",
            "ANALYZE account ACC-123"
        ]

        for message in case_variations:
            result = engine.analyze_intent(message)
            assert result.primary_intent == IntentCategory.ACCOUNT_ANALYSIS
            assert result.confidence_score > 0.7

    def test_malformed_account_ids(self, engine):
        """Test handling of malformed or incomplete account IDs."""
        malformed_cases = [
            "Analyze account ACC",  # Incomplete
            "Check ACC-",  # Truncated
            "Review account ABC-XYZ",  # Non-numeric
            "Get info for ACC123",  # Missing hyphen
            "Show account 12-34",  # Multiple hyphens
            "Analyze ACC-",  # Just prefix
        ]

        for message in malformed_cases:
            result = engine.analyze_intent(message)
            # Should still detect account analysis intent but with lower confidence
            if result.confidence_score > 0.3:
                assert result.primary_intent == IntentCategory.ACCOUNT_ANALYSIS


class TestPerformanceAndMetrics(TestIntentDetectionEngine):
    """Test performance characteristics and metrics collection."""

    def test_processing_performance(self, engine):
        """Test processing time performance."""
        test_messages = [
            "Hello",
            "Analyze account ACC-123 for risks",
            "Show historical trends for performance metrics",
            "Connect to Zoho CRM for data import",
            "What are customer retention best practices?"
        ]

        processing_times = []
        for message in test_messages:
            start_time = time.time()
            result = engine.analyze_intent(message)
            processing_time = (time.time() - start_time) * 1000
            processing_times.append(processing_time)

            assert result.processing_time_ms > 0
            assert result.processing_time_ms < 1000  # Each should be under 1 second

        # Average should be reasonable
        avg_time = sum(processing_times) / len(processing_times)
        assert avg_time < 100  # Average under 100ms

    def test_analysis_metadata(self, engine):
        """Test analysis metadata population."""
        message = "Analyze account ACC-123 for risks"
        result = engine.analyze_intent(message)

        # Check metadata fields
        assert result.analysis_id.startswith("intent_")
        assert len(result.analysis_id) == 15  # "intent_" + 8 chars
        assert result.analyzed_at is not None
        assert result.message_length == len(message)
        assert result.processing_time_ms >= 0
        assert isinstance(result.processing_time_ms, int)

        # Check confidence level calculation
        assert result.confidence_level == result.get_confidence_level()

    def test_signal_detection_completeness(self, engine):
        """Test signal detection and completeness."""
        message = "Analyze account ACC-123 for Zoho CRM data and historical trends"
        result = engine.analyze_intent(message)

        # Should detect multiple types of signals
        assert len(result.signals_detected) > 0
        assert len(result.keywords_matched) > 0
        assert len(result.patterns_matched) > 0

        # Check signal structure
        for signal in result.signals_detected:
            assert 'type' in signal
            assert 'confidence' in signal
            assert 'category' in signal
            assert isinstance(signal['confidence'], (int, float))
            assert 0 <= signal['confidence'] <= 1

    def test_batch_processing_performance(self, engine):
        """Test performance with batch processing."""
        messages = [
            f"Analyze account ACC-{i:03d} for risks" for i in range(100)
        ]

        start_time = time.time()
        results = [engine.analyze_intent(msg) for msg in messages]
        total_time = time.time() - start_time

        # Should process 100 messages efficiently
        assert total_time < 5.0  # Under 5 seconds for 100 messages
        assert len(results) == 100

        # All should have detected account analysis
        account_count = sum(1 for r in results if r.primary_intent == IntentCategory.ACCOUNT_ANALYSIS)
        assert account_count >= 90  # At least 90% should be correct


class TestEngineConfiguration(TestIntentDetectionEngine):
    """Test engine configuration and customization."""

    def test_confidence_threshold_effects(self, engine, high_threshold_engine, low_threshold_engine):
        """Test different confidence thresholds."""
        medium_confidence_message = "check customer account performance"

        # Test with different thresholds
        normal_result = engine.analyze_intent(medium_confidence_message)
        high_result = high_threshold_engine.analyze_intent(medium_confidence_message)
        low_result = low_threshold_engine.analyze_intent(medium_confidence_message)

        # Should detect same intent but routing may differ
        assert normal_result.primary_intent == high_result.primary_intent == low_result.primary_intent

        # Routing decisions should differ based on thresholds
        assert low_result.requires_account_data == True  # Low threshold = more permissive
        assert high_result.requires_account_data == False  # High threshold = more restrictive

    def test_keyword_patterns_validation(self):
        """Test keyword patterns are properly configured."""
        patterns = KeywordPatterns()

        # Check that keyword dictionaries exist
        assert hasattr(patterns, 'ACCOUNT_KEYWORDS')
        assert hasattr(patterns, 'ZOHO_KEYWORDS')
        assert hasattr(patterns, 'MEMORY_KEYWORDS')
        assert hasattr(patterns, 'GENERAL_KEYWORDS')

        # Check that patterns exist
        assert hasattr(patterns, 'PATTERNS')
        assert 'account_id_pattern' in patterns.PATTERNS
        assert 'account_review_pattern' in patterns.PATTERNS
        assert 'zoho_query_pattern' in patterns.PATTERNS

    def test_engine_initialization(self):
        """Test engine initialization with various parameters."""
        # Default initialization
        engine1 = IntentDetectionEngine()
        assert engine1.confidence_threshold == 0.5

        # Custom threshold
        engine2 = IntentDetectionEngine(confidence_threshold=0.7)
        assert engine2.confidence_threshold == 0.7

        # Edge case thresholds
        engine3 = IntentDetectionEngine(confidence_threshold=0.0)
        assert engine3.confidence_threshold == 0.0

        engine4 = IntentDetectionEngine(confidence_threshold=1.0)
        assert engine4.confidence_threshold == 1.0


class TestSupportedIntentsDocumentation(TestIntentDetectionEngine):
    """Test supported intents documentation and examples."""

    def test_get_supported_intents_structure(self, engine):
        """Test getting supported intents information structure."""
        supported_intents = engine.get_supported_intents()

        assert isinstance(supported_intents, list)
        assert len(supported_intents) >= 5  # Should support at least 5 intent types

        required_fields = ['category', 'description', 'examples', 'requires_account_data', 'calls_zoho_agent', 'calls_memory_agent']

        for intent_info in supported_intents:
            # Check all required fields exist
            for field in required_fields:
                assert field in intent_info, f"Missing field '{field}' in intent info"

            # Check data types
            assert isinstance(intent_info['examples'], list)
            assert len(intent_info['examples']) > 0
            assert isinstance(intent_info['requires_account_data'], bool)
            assert isinstance(intent_info['calls_zoho_agent'], bool)
            assert isinstance(intent_info['calls_memory_agent'], bool)

    def test_example_validation(self, engine):
        """Test that provided examples work correctly."""
        supported_intents = engine.get_supported_intents()

        for intent_info in supported_intents:
            category = intent_info['category']
            examples = intent_info['examples']

            for example in examples:
                result = engine.analyze_intent(example)

                # Example should produce expected category (with reasonable confidence)
                if result.confidence_score >= 0.5:
                    assert result.primary_intent == category, f"Example '{example}' should produce {category}, got {result.primary_intent}"

                # All examples should produce valid results
                assert isinstance(result, IntentResult)
                assert isinstance(result.confidence_score, float)
                assert 0.0 <= result.confidence_score <= 1.0

    def test_intent_categories_completeness(self, engine):
        """Test that all intent categories are covered in documentation."""
        supported_intents = engine.get_supported_intents()
        documented_categories = {intent['category'] for intent in supported_intents}

        # Check that main categories are documented
        expected_categories = {
            IntentCategory.ACCOUNT_ANALYSIS,
            IntentCategory.ZOHO_SPECIFIC,
            IntentCategory.MEMORY_HISTORY,
            IntentCategory.HELP_ASSISTANCE,
            IntentCategory.GENERAL_CONVERSATION
        }

        for category in expected_categories:
            assert category in documented_categories, f"Category {category} not documented"


# Integration-style tests
class TestRealWorldScenarios(TestIntentDetectionEngine):
    """Test real-world usage scenarios."""

    def test_customer_service_conversation(self, engine):
        """Test typical customer service conversation flow."""
        conversation = [
            "Hello, I need help with account analysis",
            "Can you analyze account ACC-12345 for me?",
            "What are the main risk factors?",
            "Show me historical performance trends",
            "What do you recommend?",
            "Thank you for your help"
        ]

        results = []
        for message in conversation:
            result = engine.analyze_intent(message)
            results.append(result)

        # Verify conversation flow detection
        assert results[0].primary_intent == IntentCategory.HELP_ASSISTANCE  # Initial help request
        assert results[1].primary_intent == IntentCategory.ACCOUNT_ANALYSIS  # Specific account
        assert results[2].primary_intent == IntentCategory.ACCOUNT_ANALYSIS  # Follow-up analysis
        assert results[3].primary_intent == IntentCategory.MEMORY_HISTORY   # Historical request
        assert results[4].primary_intent == IntentCategory.ACCOUNT_ANALYSIS  # Recommendations
        assert results[5].primary_intent == IntentCategory.GENERAL_CONVERSATION  # Thanks

    def test_sales_representative_workflow(self, engine):
        """Test sales representative typical workflow."""
        sales_workflow = [
            "Show me high-risk accounts in my portfolio",
            "Analyze account ACC-789 for retention probability",
            "Compare with historical performance data",
            "Get recommendations for account ACC-456",
            "Export data to Zoho CRM"
        ]

        results = []
        routing_decisions = []
        for message in sales_workflow:
            result = engine.analyze_intent(message)
            results.append(result)
            routing_decisions.append({
                'requires_account_data': engine.requires_account_data(result),
                'calls_zoho': engine.should_call_zoho_agent(result),
                'calls_memory': engine.should_call_memory_agent(result)
            })

        # Verify workflow detection
        assert results[0].primary_intent == IntentCategory.ACCOUNT_ANALYSIS
        assert results[1].primary_intent == IntentCategory.ACCOUNT_ANALYSIS
        assert results[2].primary_intent == IntentCategory.MEMORY_HISTORY
        assert results[3].primary_intent == IntentCategory.ACCOUNT_ANALYSIS
        assert results[4].primary_intent == IntentCategory.ZOHO_SPECIFIC

        # Verify routing decisions
        assert routing_decisions[0]['requires_account_data'] == True
        assert routing_decisions[1]['calls_zoho'] == True
        assert routing_decisions[2]['calls_memory'] == True
        assert routing_decisions[4]['calls_zoho'] == True

    def test_mixed_intent_scenarios(self, engine):
        """Test messages with mixed or ambiguous intents."""
        mixed_messages = [
            "Help me understand account ACC-123 risks using historical data",
            "What can Zoho CRM tell me about customer trends?",
            "Analyze performance and connect to CRM system",
            "Show me both current status and historical patterns for account ACC-456"
        ]

        for message in mixed_messages:
            result = engine.analyze_intent(message)

            # Should detect clear intent despite mixed signals
            assert result.confidence_score >= 0.5
            assert result.primary_intent != IntentCategory.UNKNOWN

            # Should make reasonable routing decisions
            routing_count = sum([
                engine.requires_account_data(result),
                engine.should_call_zoho_agent(result),
                engine.should_call_memory_agent(result)
            ])
            assert routing_count >= 1  # Should route to at least one agent


if __name__ == "__main__":
    # Run tests with comprehensive coverage
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--cov=src.agents.intent_detection",
        "--cov-report=html:htmlcov_intent_engine",
        "--cov-report=term-missing"
    ])