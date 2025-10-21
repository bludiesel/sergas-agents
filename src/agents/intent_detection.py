"""Intent Detection Engine for Sergas Orchestrator.

Phase 1: Foundation - Intelligent routing system for determining whether user messages
require account-specific analysis or can be handled as general conversation.

This engine analyzes user messages using keyword matching, pattern recognition, and
semantic analysis to determine intent and make routing decisions in the orchestrator.
"""

import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


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
    VERY_HIGH = "very_high"    # 0.9 - 1.0
    HIGH = "high"             # 0.7 - 0.9
    MEDIUM = "medium"         # 0.5 - 0.7
    LOW = "low"              # 0.3 - 0.5
    VERY_LOW = "very_low"    # 0.0 - 0.3


@dataclass
class IntentSignal:
    """Individual signal detected during intent analysis."""
    signal_type: str
    confidence: float
    category: IntentCategory
    matched_patterns: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate signal data."""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if not self.signal_type:
            raise ValueError("Signal type cannot be empty")


class IntentResult(BaseModel):
    """Complete intent analysis result."""
    # Primary classification
    primary_intent: IntentCategory = Field(..., description="Primary intent category")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence score")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence level category")

    # Analysis details
    signals_detected: List[Dict[str, Any]] = Field(default_factory=list, description="Individual signals detected")
    keywords_matched: List[str] = Field(default_factory=list, description="Keywords matched")
    patterns_matched: List[str] = Field(default_factory=list, description="Patterns matched")

    # Routing decisions
    requires_account_data: bool = Field(default=False, description="Needs specific account data")
    should_call_zoho_agent: bool = Field(default=False, description="Should route to Zoho agent")
    should_call_memory_agent: bool = Field(default=False, description="Should route to Memory agent")

    # Metadata
    analysis_id: str = Field(default_factory=lambda: f"intent_{uuid.uuid4().hex[:8]}", description="Unique analysis ID")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    message_length: int = Field(..., description="Original message length")
    processing_time_ms: int = Field(default=0, description="Processing time in milliseconds")

    def get_confidence_level(self) -> ConfidenceLevel:
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
    """Advanced intent detection engine for Sergas Orchestrator.

    Analyzes user messages using multiple detection strategies:
    1. Keyword matching with weighted scoring
    2. Pattern recognition with regex
    3. Semantic analysis using context
    4. Confidence scoring with multi-factor consideration

    Primary purpose: Enable intelligent routing in orchestrator without requiring
    account_id for all conversations.
    """

    def __init__(self, confidence_threshold: float = 0.5):
        """Initialize intent detection engine.

        Args:
            confidence_threshold: Minimum confidence threshold for routing decisions (default: 0.5)
        """
        self.confidence_threshold = confidence_threshold
        self.patterns = KeywordPatterns()
        self.logger = logger.bind(component="intent_detection_engine")

        # Category weights for scoring
        self.category_weights = {
            IntentCategory.ACCOUNT_ANALYSIS: 1.0,
            IntentCategory.ZOHO_SPECIFIC: 0.9,
            IntentCategory.MEMORY_HISTORY: 0.8,
            IntentCategory.HELP_ASSISTANCE: 0.6,
            IntentCategory.GENERAL_CONVERSATION: 0.4
        }

        self.logger.info("intent_detection_engine_initialized", confidence_threshold=confidence_threshold)

    def analyze_intent(self, message: str) -> IntentResult:
        """Analyze user message to determine intent and routing decisions.

        This is the primary method that orchestrates all intent detection logic.

        Args:
            message: User message to analyze

        Returns:
            IntentResult with classification and routing decisions

        Example:
            >>> engine = IntentDetectionEngine()
            >>> result = engine.analyze_intent("Analyze account ACC-123 for risk factors")
            >>> print(result.primary_intent)  # IntentCategory.ACCOUNT_ANALYSIS
            >>> print(result.should_call_zoho_agent)  # True
        """
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

        self.logger.info(
            "intent_analysis_completed",
            analysis_id=result.analysis_id,
            primary_intent=primary_intent,
            confidence=confidence_score,
            processing_time_ms=result.processing_time_ms
        )

        return result

    def requires_account_data(self, intent: IntentResult) -> bool:
        """Determine if intent requires account-specific data.

        Args:
            intent: Intent analysis result

        Returns:
            True if account data is required
        """
        return intent.requires_account_data

    def should_call_zoho_agent(self, intent: IntentResult) -> bool:
        """Determine if Zoho agent should be called.

        Args:
            intent: Intent analysis result

        Returns:
            True if Zoho agent routing is recommended
        """
        return intent.should_call_zoho_agent

    def should_call_memory_agent(self, intent: IntentResult) -> bool:
        """Determine if Memory agent should be called.

        Args:
            intent: Intent analysis result

        Returns:
            True if Memory agent routing is recommended
        """
        return intent.should_call_memory_agent

    def _normalize_message(self, message: str) -> str:
        """Normalize message for analysis.

        Args:
            message: Original message

        Returns:
            Normalized message
        """
        if not message:
            return ""

        # Convert to lowercase and strip
        normalized = message.lower().strip()

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized

    def _detect_keyword_signals(self, message: str) -> List[Dict[str, Any]]:
        """Detect keyword-based signals.

        Args:
            message: Normalized message

        Returns:
            List of keyword signals
        """
        signals = []

        # Check each keyword category
        all_keywords = {
            IntentCategory.ACCOUNT_ANALYSIS: self.patterns.ACCOUNT_KEYWORDS,
            IntentCategory.ZOHO_SPECIFIC: self.patterns.ZOHO_KEYWORDS,
            IntentCategory.MEMORY_HISTORY: self.patterns.MEMORY_KEYWORDS,
            IntentCategory.GENERAL_CONVERSATION: self.patterns.GENERAL_KEYWORDS
        }

        for category, keyword_groups in all_keywords.items():
            category_score = 0
            matched_keywords = []

            for group, keywords in keyword_groups.items():
                for keyword in keywords:
                    if keyword in message:
                        weight = self._get_keyword_weight(keyword, group)
                        category_score += weight
                        matched_keywords.append(keyword)

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
        """Detect pattern-based signals using regex.

        Args:
            message: Normalized message

        Returns:
            List of pattern signals
        """
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

        # Question pattern
        if self.patterns.PATTERNS['question_pattern'].search(message):
            signals.append({
                'type': 'pattern',
                'confidence': 0.4,
                'category': IntentCategory.GENERAL_CONVERSATION,
                'pattern': 'question_pattern',
                'details': {'description': 'Question format detected'}
            })

        return signals

    def _detect_semantic_signals(self, message: str) -> List[Dict[str, Any]]:
        """Detect semantic signals using context analysis.

        Args:
            message: Normalized message

        Returns:
            List of semantic signals
        """
        signals = []

        # Message length analysis
        if len(message) > 100:
            # Longer messages tend to be more specific
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
        """Calculate primary intent from signals.

        Args:
            signals: List of detected signals

        Returns:
            Tuple of (primary_intent, confidence_score)
        """
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
        """Make routing decisions based on intent analysis.

        Args:
            primary_intent: Primary intent category
            confidence: Confidence score
            signals: All detected signals

        Returns:
            Dictionary of routing decisions
        """
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

        # Help/General routing - no specialized agents needed
        elif primary_intent in [IntentCategory.HELP_ASSISTANCE, IntentCategory.GENERAL_CONVERSATION]:
            # No specialized routing needed
            pass

        return routing

    def _get_keyword_weight(self, keyword: str, group: str) -> float:
        """Get weight for keyword based on importance.

        Args:
            keyword: The keyword
            group: Keyword group

        Returns:
            Weight value (0.0 - 1.0)
        """
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
        """Convert confidence score to confidence level.

        Args:
            confidence: Confidence score (0.0 - 1.0)

        Returns:
            Confidence level enum
        """
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

    def get_supported_intents(self) -> List[Dict[str, Any]]:
        """Get list of supported intent categories with descriptions.

        Returns:
            List of intent information
        """
        return [
            {
                'category': IntentCategory.ACCOUNT_ANALYSIS,
                'description': 'Account-specific analysis, review, or assessment requests',
                'examples': [
                    'Analyze account ACC-123 for risk factors',
                    'Review customer health status',
                    'Check account performance metrics'
                ],
                'requires_account_data': True,
                'calls_zoho_agent': True,
                'calls_memory_agent': False
            },
            {
                'category': IntentCategory.ZOHO_SPECIFIC,
                'description': 'Zoho CRM or integration-related questions',
                'examples': [
                    'Connect Zoho CRM to get account data',
                    'What Zoho modules are available?',
                    'Import data from Zoho'
                ],
                'requires_account_data': False,
                'calls_zoho_agent': True,
                'calls_memory_agent': False
            },
            {
                'category': IntentCategory.MEMORY_HISTORY,
                'description': 'Historical data, trends, or pattern analysis requests',
                'examples': [
                    'Show historical trends for this account',
                    'Compare performance over last quarter',
                    'What patterns do we see in the data?'
                ],
                'requires_account_data': False,
                'calls_zoho_agent': False,
                'calls_memory_agent': True
            },
            {
                'category': IntentCategory.HELP_ASSISTANCE,
                'description': 'Help requests or guidance questions',
                'examples': [
                    'How do I analyze account risks?',
                    'Can you help me understand the dashboard?',
                    'What features are available?'
                ],
                'requires_account_data': False,
                'calls_zoho_agent': False,
                'calls_memory_agent': False
            },
            {
                'category': IntentCategory.GENERAL_CONVERSATION,
                'description': 'General questions or conversation',
                'examples': [
                    'Hello, how are you?',
                    'What can you do?',
                    'Thank you for your help'
                ],
                'requires_account_data': False,
                'calls_zoho_agent': False,
                'calls_memory_agent': False
            }
        ]

    def __repr__(self) -> str:
        """String representation."""
        return f"<IntentDetectionEngine confidence_threshold={self.confidence_threshold}>"