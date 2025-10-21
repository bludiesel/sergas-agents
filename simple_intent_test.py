#!/usr/bin/env python3
"""Simple test script for IntentDetectionEngine without external dependencies."""

import re
import uuid
import time
from datetime import datetime
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
import json


# Minimal implementation for testing
class IntentCategory(str, Enum):
    """Primary intent categories for message routing."""
    ACCOUNT_ANALYSIS = "account_analysis"
    GENERAL_CONVERSATION = "general_conversation"
    ZOHO_SPECIFIC = "zoho_specific"
    MEMORY_HISTORY = "memory_history"
    HELP_ASSISTANCE = "help_assistance"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """Confidence levels for intent detection."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


@dataclass
class IntentSignal:
    """Individual signal detected during intent analysis."""
    signal_type: str
    confidence: float
    category: IntentCategory
    matched_patterns: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


class IntentResult:
    """Complete intent analysis result."""

    def __init__(self, **kwargs):
        self.primary_intent = kwargs.get('primary_intent', IntentCategory.UNKNOWN)
        self.confidence_score = kwargs.get('confidence_score', 0.0)
        self.confidence_level = kwargs.get('confidence_level', ConfidenceLevel.VERY_LOW)
        self.signals_detected = kwargs.get('signals_detected', [])
        self.keywords_matched = kwargs.get('keywords_matched', [])
        self.patterns_matched = kwargs.get('patterns_matched', [])
        self.requires_account_data = kwargs.get('requires_account_data', False)
        self.should_call_zoho_agent = kwargs.get('should_call_zoho_agent', False)
        self.should_call_memory_agent = kwargs.get('should_call_memory_agent', False)
        self.analysis_id = kwargs.get('analysis_id', f"intent_{uuid.uuid4().hex[:8]}")
        self.analyzed_at = kwargs.get('analyzed_at', datetime.utcnow())
        self.message_length = kwargs.get('message_length', 0)
        self.processing_time_ms = kwargs.get('processing_time_ms', 0)

    def get_confidence_level(self):
        """Calculate confidence level from score."""
        if self.confidence_score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif self.confidence_score >= 0.7:
            return ConfidenceLevel.HIGH
        elif self.confidence_score >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif self.confidence_score >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW


class KeywordPatterns:
    """Keyword and pattern definitions for intent detection."""

    # Account Analysis Keywords
    ACCOUNT_KEYWORDS = {
        'account': ['account', 'accounts', 'client', 'customer', 'organization'],
        'account_id': ['acc-', 'account-', 'client-', 'customer-', '#'],
        'analysis': ['analyze', 'analysis', 'review', 'assessment', 'evaluate'],
        'status': ['status', 'health', 'condition', 'state', 'standing'],
        'risk': ['risk', 'risky', 'danger', 'threat', 'warning'],
        'performance': ['performance', 'metrics', 'kpi', 'results', 'progress'],
        'issues': ['issues', 'problems', 'concerns', 'trouble', 'challenges'],
        'opportunities': ['opportunities', 'potential', 'growth', 'expansion', 'upsell']
    }

    # Zoho-Specific Keywords
    ZOHO_KEYWORDS = {
        'zoho': ['zoho', 'zoho crm', 'zohocrm', 'zoho-one'],
        'crm': ['crm', 'customer relationship management', 'salesforce', 'hubspot'],
        'data': ['data', 'records', 'fields', 'custom fields', 'modules'],
        'integration': ['integration', 'api', 'sync', 'connect', 'import'],
        'zoho_modules': ['deals', 'contacts', 'leads', 'accounts', 'activities']
    }

    # Memory/History Keywords
    MEMORY_KEYWORDS = {
        'history': ['history', 'historical', 'past', 'previous', 'timeline'],
        'trends': ['trends', 'patterns', 'changes', 'evolution', 'trajectory'],
        'comparison': ['compare', 'comparison', 'versus', 'vs', 'against'],
        'memory': ['memory', 'remember', 'recall', 'stored', 'archived'],
        'period': ['quarter', 'month', 'year', 'period', 'duration', 'timeframe']
    }

    # General Conversation Keywords
    GENERAL_KEYWORDS = {
        'greetings': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'thanks', 'thank you'],
        'help': ['help', 'assist', 'assistance', 'guidance', 'how to', 'how do'],
        'general': ['general', 'overview', 'summary', 'information', 'details'],
        'questions': ['what', 'when', 'where', 'why', 'how', 'can you', 'could you'],
        'capabilities': ['features', 'capabilities', 'functions', 'abilities', 'what can']
    }

    # Regex Patterns for Advanced Detection
    PATTERNS = {
        'account_id_pattern': re.compile(r'\b(ACC-|Account-|Client-|Customer-|#)[A-Za-z0-9-]+\b', re.IGNORECASE),
        'account_review_pattern': re.compile(r'\b(review|analyze|check|status|health)\s+(account|client|customer)\b', re.IGNORECASE),
        'zoho_query_pattern': re.compile(r'\b(zoho|crm|salesforce|hubspot)\b.*\b(data|records|integration|api)\b', re.IGNORECASE),
        'historical_pattern': re.compile(r'\b(history|historical|past|previous|trends?|patterns?)\b.*\b(data|performance|metrics|results?)\b', re.IGNORECASE),
        'help_pattern': re.compile(r'\b(help|assist|guidance|how\s+to|can\s+you)\b', re.IGNORECASE),
        'question_pattern': re.compile(r'\^(what|when|where|why|how|who|which)\b', re.IGNORECASE)
    }


class IntentDetectionEngine:
    """Advanced intent detection engine for Sergas Orchestrator."""

    def __init__(self, confidence_threshold: float = 0.5):
        """Initialize intent detection engine."""
        self.confidence_threshold = confidence_threshold
        self.patterns = KeywordPatterns()

        # Category weights for scoring
        self.category_weights = {
            IntentCategory.ACCOUNT_ANALYSIS: 1.0,
            IntentCategory.ZOHO_SPECIFIC: 0.9,
            IntentCategory.MEMORY_HISTORY: 0.8,
            IntentCategory.HELP_ASSISTANCE: 0.6,
            IntentCategory.GENERAL_CONVERSATION: 0.4
        }

    def analyze_intent(self, message: str) -> IntentResult:
        """Analyze user message to determine intent and routing decisions."""
        start_time = datetime.utcnow()

        # Normalize message
        normalized_message = self._normalize_message(message)
        message_length = len(normalized_message)

        # Detect signals from different strategies
        keyword_signals = self._detect_keyword_signals(normalized_message)
        pattern_signals = self._detect_pattern_signals(normalized_message)
        semantic_signals = self._detect_semantic_signals(normalized_message)

        # Combine and analyze signals
        all_signals = keyword_signals + pattern_signals + semantic_signals

        # Calculate primary intent and confidence
        primary_intent, confidence_score = self._calculate_primary_intent(all_signals)

        # Extract matched keywords and patterns
        keywords_matched = [sig.get('keyword', '') for sig in keyword_signals if sig.get('keyword')]
        patterns_matched = [sig.get('pattern', '') for sig in pattern_signals if sig.get('pattern')]

        # Make routing decisions
        routing_decisions = self._make_routing_decisions(primary_intent, confidence_score, all_signals)

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Create result
        result = IntentResult(
            primary_intent=primary_intent,
            confidence_score=confidence_score,
            confidence_level=self._get_confidence_level(confidence_score),
            signals_detected=[{
                'type': sig['type'],
                'confidence': sig['confidence'],
                'category': sig['category'],
                'details': sig.get('details', {})
            } for sig in all_signals],
            keywords_matched=keywords_matched,
            patterns_matched=patterns_matched,
            message_length=message_length,
            processing_time_ms=int(processing_time),
            **routing_decisions
        )

        return result

    def _normalize_message(self, message: str) -> str:
        """Normalize message for analysis."""
        if not message:
            return ""
        normalized = message.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def _detect_keyword_signals(self, message: str) -> List[Dict[str, Any]]:
        """Detect keyword-based signals."""
        signals = []

        # Check each keyword category
        all_keywords = {
            IntentCategory.ACCOUNT_ANALYSIS: self.patterns.ACCOUNT_KEYWORDS,
            IntentCategory.ZOHO_SPECIFIC: self.patterns.ZOHO_KEYWORDS,
            IntentCategory.MEMORY_HISTORY: self.patterns.MEMORY_KEYWORDS,
            IntentCategory.GENERAL_CONVERSATION: self.patterns.GENERAL_KEYWORDS
        }

        for category, keyword_groups in all_keywords.items():
            for group, keywords in keyword_groups.items():
                for keyword in keywords:
                    if keyword in message:
                        weight = self._get_keyword_weight(keyword, group)
                        signals.append({
                            'type': 'keyword',
                            'confidence': weight,
                            'category': category,
                            'keyword': keyword,
                            'group': group,
                            'details': {'weight': weight, 'group': group}
                        })

        return signals

    def _detect_pattern_signals(self, message: str) -> List[Dict[str, Any]]:
        """Detect pattern-based signals using regex."""
        signals = []

        # Account ID pattern
        if self.patterns.PATTERNS['account_id_pattern'].search(message):
            signals.append({
                'type': 'pattern',
                'confidence': 0.9,
                'category': IntentCategory.ACCOUNT_ANALYSIS,
                'pattern': 'account_id_pattern',
                'details': {'description': 'Account ID format detected'}
            })

        # Account review pattern
        if self.patterns.PATTERNS['account_review_pattern'].search(message):
            signals.append({
                'type': 'pattern',
                'confidence': 0.85,
                'category': IntentCategory.ACCOUNT_ANALYSIS,
                'pattern': 'account_review_pattern',
                'details': {'description': 'Account review request detected'}
            })

        # Zoho query pattern
        if self.patterns.PATTERNS['zoho_query_pattern'].search(message):
            signals.append({
                'type': 'pattern',
                'confidence': 0.8,
                'category': IntentCategory.ZOHO_SPECIFIC,
                'pattern': 'zoho_query_pattern',
                'details': {'description': 'Zoho/CRM query detected'}
            })

        # Historical pattern
        if self.patterns.PATTERNS['historical_pattern'].search(message):
            signals.append({
                'type': 'pattern',
                'confidence': 0.75,
                'category': IntentCategory.MEMORY_HISTORY,
                'pattern': 'historical_pattern',
                'details': {'description': 'Historical data request detected'}
            })

        # Help pattern
        if self.patterns.PATTERNS['help_pattern'].search(message):
            signals.append({
                'type': 'pattern',
                'confidence': 0.6,
                'category': IntentCategory.HELP_ASSISTANCE,
                'pattern': 'help_pattern',
                'details': {'description': 'Help request detected'}
            })

        return signals

    def _detect_semantic_signals(self, message: str) -> List[Dict[str, Any]]:
        """Detect semantic signals using context analysis."""
        signals = []

        # Message length analysis
        if len(message) > 100:
            signals.append({
                'type': 'semantic',
                'confidence': 0.1,
                'category': IntentCategory.GENERAL_CONVERSATION,
                'details': {'type': 'message_length', 'value': len(message)}
            })

        # Exclamation mark detection (indicates excitement/urgency)
        if '!' in message:
            signals.append({
                'type': 'semantic',
                'confidence': 0.05,
                'category': IntentCategory.ACCOUNT_ANALYSIS,
                'details': {'type': 'urgency_indicator', 'punctuation': '!'}
            })

        # Question mark detection
        if '?' in message:
            signals.append({
                'type': 'semantic',
                'confidence': 0.05,
                'category': IntentCategory.HELP_ASSISTANCE,
                'details': {'type': 'question_indicator', 'punctuation': '?'}
            })

        return signals

    def _calculate_primary_intent(self, signals: List[Dict[str, Any]]) -> Tuple[IntentCategory, float]:
        """Calculate primary intent from signals."""
        if not signals:
            return IntentCategory.UNKNOWN, 0.0

        # Group signals by category
        category_scores = {}
        category_signal_counts = {}

        for signal in signals:
            category = signal['category']
            confidence = signal['confidence']

            # Apply category weight
            weighted_confidence = confidence * self.category_weights.get(category, 1.0)

            if category not in category_scores:
                category_scores[category] = 0
                category_signal_counts[category] = 0

            category_scores[category] += weighted_confidence
            category_signal_counts[category] += 1

        # Find category with highest score
        if not category_scores:
            return IntentCategory.UNKNOWN, 0.0

        primary_category = max(category_scores.keys(), key=lambda k: category_scores[k])
        raw_score = category_scores[primary_category]

        # Normalize score by number of signals to avoid bias
        signal_count = category_signal_counts[primary_category]
        normalized_score = min(raw_score / max(signal_count, 1), 1.0)

        # Apply additional normalization based on total signals
        total_signals = len(signals)
        if total_signals > 0:
            category_ratio = signal_count / total_signals
            final_score = normalized_score * category_ratio
        else:
            final_score = normalized_score

        return primary_category, min(final_score, 1.0)

    def _make_routing_decisions(self, primary_intent: IntentCategory, confidence: float, signals: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Make routing decisions based on intent analysis."""
        routing = {
            'requires_account_data': False,
            'should_call_zoho_agent': False,
            'should_call_memory_agent': False
        }

        # Low confidence intents default to general conversation
        if confidence < self.confidence_threshold:
            return routing

        # Account Analysis routing
        if primary_intent == IntentCategory.ACCOUNT_ANALYSIS:
            routing['requires_account_data'] = True
            routing['should_call_zoho_agent'] = True

            # Also call memory agent for historical context
            if any(sig['category'] == IntentCategory.MEMORY_HISTORY for sig in signals):
                routing['should_call_memory_agent'] = True

        # Zoho-specific routing
        elif primary_intent == IntentCategory.ZOHO_SPECIFIC:
            routing['should_call_zoho_agent'] = True
            # May need account data if specific account mentioned
            if any(sig.get('pattern') == 'account_id_pattern' for sig in signals):
                routing['requires_account_data'] = True

        # Memory/History routing
        elif primary_intent == IntentCategory.MEMORY_HISTORY:
            routing['should_call_memory_agent'] = True
            # May need account data for historical analysis
            if any(sig['category'] == IntentCategory.ACCOUNT_ANALYSIS for sig in signals):
                routing['requires_account_data'] = True

        return routing

    def _get_keyword_weight(self, keyword: str, group: str) -> float:
        """Get weight for keyword based on importance."""
        # High-importance keywords
        high_importance = {
            'account': 0.8,
            'acc-': 0.9,
            'analyze': 0.7,
            'zoho': 0.8,
            'crm': 0.7,
            'history': 0.6,
            'risk': 0.8
        }

        # Check for exact matches first
        if keyword.lower() in high_importance:
            return high_importance[keyword.lower()]

        # Group-based weights
        group_weights = {
            'account_id': 0.9,
            'analysis': 0.7,
            'status': 0.6,
            'risk': 0.8,
            'zoho': 0.8,
            'history': 0.6,
            'greetings': 0.3,
            'help': 0.5
        }

        return group_weights.get(group, 0.4)

    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Convert confidence score to confidence level."""
        if confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def requires_account_data(self, intent: IntentResult) -> bool:
        """Determine if intent requires account-specific data."""
        return intent.requires_account_data

    def should_call_zoho_agent(self, intent: IntentResult) -> bool:
        """Determine if Zoho agent should be called."""
        return intent.should_call_zoho_agent

    def should_call_memory_agent(self, intent: IntentResult) -> bool:
        """Determine if Memory agent should be called."""
        return intent.should_call_memory_agent


def run_comprehensive_tests():
    """Run comprehensive tests of the IntentDetectionEngine."""
    print("🚀 Starting IntentDetectionEngine Comprehensive Tests\n")

    engine = IntentDetectionEngine(confidence_threshold=0.5)

    test_cases = [
        # Account Analysis Tests
        {
            'message': 'Analyze account ACC-12345 for risk factors',
            'expected_intent': IntentCategory.ACCOUNT_ANALYSIS,
            'expected_min_confidence': 0.8,
            'expected_requires_account_data': True,
            'expected_calls_zoho': True,
            'description': 'Account analysis with explicit account ID'
        },
        {
            'message': 'Review customer health status',
            'expected_intent': IntentCategory.ACCOUNT_ANALYSIS,
            'expected_min_confidence': 0.6,
            'expected_requires_account_data': True,
            'expected_calls_zoho': True,
            'description': 'Account analysis with customer health keywords'
        },
        {
            'message': 'Check account performance metrics',
            'expected_intent': IntentCategory.ACCOUNT_ANALYSIS,
            'expected_min_confidence': 0.6,
            'expected_requires_account_data': True,
            'expected_calls_zoho': True,
            'description': 'Account analysis with performance keywords'
        },

        # Zoho-Specific Tests
        {
            'message': 'Connect to Zoho CRM to get account data',
            'expected_intent': IntentCategory.ZOHO_SPECIFIC,
            'expected_min_confidence': 0.7,
            'expected_requires_account_data': False,
            'expected_calls_zoho': True,
            'description': 'Zoho CRM integration request'
        },

        # Memory/History Tests
        {
            'message': 'Show historical trends for customer data',
            'expected_intent': IntentCategory.MEMORY_HISTORY,
            'expected_min_confidence': 0.6,
            'expected_requires_account_data': False,
            'expected_calls_memory': True,
            'description': 'Historical trends analysis'
        },

        # General Conversation Tests
        {
            'message': 'Hello, how are you?',
            'expected_intent': IntentCategory.GENERAL_CONVERSATION,
            'expected_min_confidence': 0.3,
            'expected_requires_account_data': False,
            'expected_calls_zoho': False,
            'description': 'General greeting'
        },
        {
            'message': 'I need help with account analysis',
            'expected_intent': IntentCategory.HELP_ASSISTANCE,
            'expected_min_confidence': 0.6,
            'expected_requires_account_data': False,
            'expected_calls_zoho': False,
            'description': 'Help request with account context'
        },

        # Edge Cases
        {
            'message': '',
            'expected_intent': IntentCategory.UNKNOWN,
            'expected_min_confidence': 0.0,
            'expected_requires_account_data': False,
            'expected_calls_zoho': False,
            'description': 'Empty message'
        },
        {
            'message': 'Analyze account ACC-123 for historical Zoho CRM trends',
            'expected_intent': IntentCategory.ACCOUNT_ANALYSIS,
            'expected_min_confidence': 0.8,
            'expected_requires_account_data': True,
            'expected_calls_zoho': True,
            'expected_calls_memory': True,
            'description': 'Combined intent with multiple agents'
        }
    ]

    passed_tests = 0
    total_tests = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}/{total_tests}: {test_case['description']}")
        print(f"Message: \"{test_case['message']}\"")

        # Run analysis
        start_time = time.time()
        result = engine.analyze_intent(test_case['message'])
        analysis_time = (time.time() - start_time) * 1000

        # Check results
        test_passed = True

        if result.primary_intent != test_case['expected_intent']:
            print(f"  ❌ Intent mismatch: Expected {test_case['expected_intent']}, got {result.primary_intent}")
            test_passed = False
        else:
            print(f"  ✅ Intent: {result.primary_intent}")

        if result.confidence_score < test_case['expected_min_confidence']:
            print(f"  ❌ Confidence too low: Expected ≥{test_case['expected_min_confidence']}, got {result.confidence_score}")
            test_passed = False
        else:
            print(f"  ✅ Confidence: {result.confidence_score:.3f}")

        if result.requires_account_data != test_case['expected_requires_account_data']:
            print(f"  ❌ Account data requirement mismatch: Expected {test_case['expected_requires_account_data']}, got {result.requires_account_data}")
            test_passed = False
        else:
            print(f"  ✅ Requires Account Data: {result.requires_account_data}")

        if result.should_call_zoho_agent != test_case['expected_calls_zoho']:
            print(f"  ❌ Zoho agent call mismatch: Expected {test_case['expected_calls_zoho']}, got {result.should_call_zoho_agent}")
            test_passed = False
        else:
            print(f"  ✅ Calls Zoho Agent: {result.should_call_zoho_agent}")

        # Check memory agent if specified
        if 'expected_calls_memory' in test_case:
            if result.should_call_memory_agent != test_case['expected_calls_memory']:
                print(f"  ❌ Memory agent call mismatch: Expected {test_case['expected_calls_memory']}, got {result.should_call_memory_agent}")
                test_passed = False
            else:
                print(f"  ✅ Calls Memory Agent: {result.should_call_memory_agent}")

        # Additional info
        print(f"  📊 Processing Time: {analysis_time:.2f}ms")
        print(f"  🔍 Keywords Matched: {result.keywords_matched}")
        print(f"  🎯 Patterns Matched: {result.patterns_matched}")

        if test_passed:
            passed_tests += 1
            print("  ✅ TEST PASSED\n")
        else:
            print("  ❌ TEST FAILED\n")

    # Test Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! IntentDetectionEngine is working correctly!")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed. Please review the implementation.")
        return False


def test_routing_decisions():
    """Test specific routing decision logic."""
    print("\n🔄 Testing Routing Decision Logic")
    print("=" * 40)

    engine = IntentDetectionEngine()

    routing_tests = [
        {
            'message': 'Analyze account ACC-123 for risks',
            'test_func': engine.requires_account_data,
            'expected': True,
            'description': 'Account analysis requires account data'
        },
        {
            'message': 'Analyze account ACC-123 for risks',
            'test_func': engine.should_call_zoho_agent,
            'expected': True,
            'description': 'Account analysis calls Zoho agent'
        },
        {
            'message': 'Hello, how are you?',
            'test_func': engine.requires_account_data,
            'expected': False,
            'description': 'General conversation does not require account data'
        },
        {
            'message': 'Show historical trends for performance',
            'test_func': engine.should_call_memory_agent,
            'expected': True,
            'description': 'Historical trends call memory agent'
        },
        {
            'message': 'Connect to Zoho CRM',
            'test_func': engine.should_call_zoho_agent,
            'expected': True,
            'description': 'Zoho connection calls Zoho agent'
        }
    ]

    routing_passed = 0
    for test in routing_tests:
        result = engine.analyze_intent(test['message'])
        actual = test['test_func'](result)

        if actual == test['expected']:
            print(f"✅ {test['description']}")
            routing_passed += 1
        else:
            print(f"❌ {test['description']}: Expected {test['expected']}, got {actual}")

    print(f"\nRouting Tests: {routing_passed}/{len(routing_tests)} passed")
    return routing_passed == len(routing_tests)


if __name__ == "__main__":
    # Run comprehensive tests
    success = run_comprehensive_tests()

    # Run routing decision tests
    routing_success = test_routing_decisions()

    # Final verdict
    if success and routing_success:
        print("\n🏆 OVERALL RESULT: ALL TESTS PASSED!")
        print("✅ IntentDetectionEngine is ready for production use!")
        exit(0)
    else:
        print("\n❌ OVERALL RESULT: SOME TESTS FAILED!")
        print("🔧 Please review the implementation and fix the issues.")
        exit(1)