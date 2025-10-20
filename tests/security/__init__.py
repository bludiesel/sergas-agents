"""Security testing package for Sergas Super Account Manager.

Week 14: Security Review - Comprehensive Security Testing

This package contains comprehensive security tests covering:
- Authentication security (OAuth, JWT, sessions, permissions)
- Data protection (encryption, PII handling, audit logging, retention)
- Input validation (SQL injection, XSS, CSRF, sanitization)

Test Statistics:
- Total test classes: 14
- Total test methods: 115
- Total lines of test code: 2,887

Test Coverage:
- test_authentication.py: 35 tests covering OAuth flows, token validation,
  session security, and permission enforcement
- test_data_protection.py: 40 tests covering encryption, PII handling,
  audit logging, and data retention
- test_input_validation.py: 40 tests covering SQL injection, XSS, CSRF,
  and general input sanitization

Usage:
    # Run all security tests
    pytest tests/security/

    # Run specific test file
    pytest tests/security/test_authentication.py

    # Run with coverage
    pytest tests/security/ --cov=src --cov-report=html

    # Run specific test class
    pytest tests/security/test_authentication.py::TestOAuthFlow

    # Run specific test
    pytest tests/security/test_authentication.py::TestOAuthFlow::test_oauth_authorization_url_generation
"""

__version__ = "1.0.0"
__author__ = "Security Engineering Team"
__date__ = "2025-10-19"
