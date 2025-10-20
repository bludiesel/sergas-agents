"""Comprehensive authentication security tests.

Tests OAuth flows, token validation, session security, and permission enforcement.
Week 14: Security Review - Authentication Testing
"""

import pytest
import jwt
import hashlib
import time
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
from freezegun import freeze_time

from src.integrations.zoho.token_store import TokenStore, ZohoTokenModel
from src.integrations.zoho.sdk_client import ZohoSDKClient
from src.integrations.zoho.exceptions import ZohoAuthError, ZohoTokenError
from src.models.config import ZohoSDKConfig


# =================================================================
# Test Fixtures
# =================================================================

@pytest.fixture
def db_url():
    """Test database URL."""
    return "postgresql://test:test@localhost:5432/test_db"


@pytest.fixture
def token_store(db_url):
    """Initialize token store for testing."""
    store = TokenStore(db_url)
    yield store
    # Cleanup
    try:
        store.delete_token("oauth")
    except:
        pass


@pytest.fixture
def valid_oauth_config():
    """Valid OAuth configuration."""
    return ZohoSDKConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        refresh_token="test_refresh_token",
        redirect_url="http://localhost:8000/callback",
        region="us",
        environment="sandbox"
    )


@pytest.fixture
def valid_access_token():
    """Generate valid access token."""
    payload = {
        "sub": "test_user",
        "scope": "ZohoCRM.modules.ALL",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    return jwt.encode(payload, "test_secret", algorithm="HS256")


@pytest.fixture
def expired_access_token():
    """Generate expired access token."""
    payload = {
        "sub": "test_user",
        "scope": "ZohoCRM.modules.ALL",
        "iat": int(time.time()) - 7200,
        "exp": int(time.time()) - 3600
    }
    return jwt.encode(payload, "test_secret", algorithm="HS256")


# =================================================================
# OAuth Flow Tests (10 tests)
# =================================================================

class TestOAuthFlow:
    """Test OAuth 2.0 authorization flow."""

    def test_oauth_authorization_url_generation(self, valid_oauth_config):
        """Test OAuth authorization URL is correctly formatted."""
        # Given valid OAuth config
        config = valid_oauth_config

        # When generating authorization URL
        auth_url = self._generate_auth_url(config)

        # Then URL should contain required parameters
        assert "client_id=" in auth_url
        assert "redirect_uri=" in auth_url
        assert "response_type=code" in auth_url
        assert "scope=" in auth_url

    def test_oauth_authorization_with_pkce(self, valid_oauth_config):
        """Test OAuth flow with PKCE (Proof Key for Code Exchange)."""
        # Given PKCE challenge
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = hashlib.sha256(code_verifier.encode()).hexdigest()

        # When generating auth URL with PKCE
        auth_url = self._generate_auth_url_with_pkce(
            valid_oauth_config,
            code_challenge
        )

        # Then URL should contain PKCE parameters
        assert "code_challenge=" in auth_url
        assert "code_challenge_method=S256" in auth_url

    def test_oauth_token_exchange(self, valid_oauth_config, mocker):
        """Test exchanging authorization code for access token."""
        # Given authorization code
        auth_code = "test_auth_code_12345"

        # Mock token endpoint response
        mock_response = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        mocker.patch("requests.post", return_value=Mock(json=lambda: mock_response))

        # When exchanging code for token
        token_response = self._exchange_code_for_token(
            valid_oauth_config,
            auth_code
        )

        # Then should receive valid tokens
        assert token_response["access_token"] == "test_access_token"
        assert token_response["refresh_token"] == "test_refresh_token"
        assert token_response["expires_in"] == 3600

    def test_oauth_token_refresh(self, valid_oauth_config, token_store, mocker):
        """Test refreshing expired access token."""
        # Given expired token in store
        token_store.save_token(
            access_token="expired_token",
            refresh_token="valid_refresh_token",
            expires_in=-3600  # Already expired
        )

        # Mock refresh endpoint
        mock_response = {
            "access_token": "new_access_token",
            "expires_in": 3600
        }
        mocker.patch("requests.post", return_value=Mock(json=lambda: mock_response))

        # When refreshing token
        new_token = self._refresh_access_token(
            valid_oauth_config,
            "valid_refresh_token"
        )

        # Then should receive new access token
        assert new_token["access_token"] == "new_access_token"

    def test_oauth_invalid_client_credentials(self, mocker):
        """Test OAuth flow with invalid client credentials."""
        # Given invalid credentials
        invalid_config = ZohoSDKConfig(
            client_id="invalid_client",
            client_secret="invalid_secret",
            refresh_token="test_refresh",
            redirect_url="http://localhost:8000/callback"
        )

        # Mock error response
        mocker.patch("requests.post", return_value=Mock(
            status_code=401,
            json=lambda: {"error": "invalid_client"}
        ))

        # When attempting token exchange
        # Then should raise authentication error
        with pytest.raises(ZohoAuthError, match="invalid_client"):
            self._exchange_code_for_token(invalid_config, "auth_code")

    def test_oauth_invalid_authorization_code(self, valid_oauth_config, mocker):
        """Test OAuth with invalid authorization code."""
        # Given invalid auth code
        invalid_code = "invalid_code"

        # Mock error response
        mocker.patch("requests.post", return_value=Mock(
            status_code=400,
            json=lambda: {"error": "invalid_grant"}
        ))

        # When exchanging invalid code
        # Then should raise error
        with pytest.raises(ZohoAuthError, match="invalid_grant"):
            self._exchange_code_for_token(valid_oauth_config, invalid_code)

    def test_oauth_scope_validation(self, valid_access_token):
        """Test OAuth scope validation."""
        # Given token with specific scopes
        decoded = jwt.decode(valid_access_token, options={"verify_signature": False})

        # When checking required scope
        required_scope = "ZohoCRM.modules.ALL"

        # Then token should have required scope
        assert required_scope in decoded.get("scope", "")

    def test_oauth_token_revocation(self, valid_oauth_config, token_store, mocker):
        """Test OAuth token revocation."""
        # Given valid token
        token_store.save_token(
            access_token="revoke_me",
            refresh_token="refresh_token",
            expires_in=3600
        )

        # Mock revocation endpoint
        mocker.patch("requests.post", return_value=Mock(status_code=200))

        # When revoking token
        result = self._revoke_token(valid_oauth_config, "revoke_me")

        # Then token should be revoked
        assert result is True
        assert token_store.get_token() is None

    def test_oauth_state_parameter_validation(self, valid_oauth_config):
        """Test OAuth state parameter for CSRF protection."""
        # Given state parameter
        state = secrets.token_urlsafe(32)

        # When generating auth URL with state
        auth_url = self._generate_auth_url(valid_oauth_config, state=state)

        # Then state should be in URL
        assert f"state={state}" in auth_url

    def test_oauth_redirect_uri_validation(self, valid_oauth_config):
        """Test OAuth redirect URI validation."""
        # Given exact redirect URI
        redirect_uri = valid_oauth_config.redirect_url

        # When validating callback
        is_valid = self._validate_redirect_uri(redirect_uri, valid_oauth_config)

        # Then should be valid
        assert is_valid is True

        # When using different redirect URI
        invalid_uri = "http://evil.com/callback"
        is_valid = self._validate_redirect_uri(invalid_uri, valid_oauth_config)

        # Then should be invalid
        assert is_valid is False


# =================================================================
# Token Validation Tests (10 tests)
# =================================================================

class TestTokenValidation:
    """Test JWT and OAuth token validation."""

    def test_token_signature_validation(self, valid_access_token):
        """Test JWT signature validation."""
        # Given valid token
        token = valid_access_token

        # When validating with correct secret
        try:
            decoded = jwt.decode(token, "test_secret", algorithms=["HS256"])
            is_valid = True
        except jwt.InvalidSignatureError:
            is_valid = False

        # Then should be valid
        assert is_valid is True

    def test_token_invalid_signature(self, valid_access_token):
        """Test detection of invalid JWT signature."""
        # Given token validated with wrong secret
        # When attempting to decode with wrong secret
        # Then should raise signature error
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(valid_access_token, "wrong_secret", algorithms=["HS256"])

    def test_token_expiration_validation(self, expired_access_token):
        """Test JWT expiration validation."""
        # Given expired token
        # When validating expiration
        # Then should raise expired error
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(expired_access_token, "test_secret", algorithms=["HS256"])

    def test_token_not_before_validation(self):
        """Test JWT 'not before' (nbf) claim validation."""
        # Given token with future nbf
        future_time = int(time.time()) + 3600
        payload = {
            "sub": "test_user",
            "nbf": future_time,
            "exp": future_time + 3600
        }
        token = jwt.encode(payload, "test_secret", algorithm="HS256")

        # When validating before nbf time
        # Then should raise error
        with pytest.raises(jwt.ImmatureSignatureError):
            jwt.decode(token, "test_secret", algorithms=["HS256"])

    def test_token_audience_validation(self):
        """Test JWT audience (aud) claim validation."""
        # Given token with specific audience
        payload = {
            "sub": "test_user",
            "aud": "sergas-api",
            "exp": int(time.time()) + 3600
        }
        token = jwt.encode(payload, "test_secret", algorithm="HS256")

        # When validating with correct audience
        decoded = jwt.decode(
            token,
            "test_secret",
            algorithms=["HS256"],
            audience="sergas-api"
        )

        # Then should succeed
        assert decoded["aud"] == "sergas-api"

        # When validating with wrong audience
        # Then should raise error
        with pytest.raises(jwt.InvalidAudienceError):
            jwt.decode(
                token,
                "test_secret",
                algorithms=["HS256"],
                audience="wrong-audience"
            )

    def test_token_issuer_validation(self):
        """Test JWT issuer (iss) claim validation."""
        # Given token with specific issuer
        payload = {
            "sub": "test_user",
            "iss": "sergas-auth",
            "exp": int(time.time()) + 3600
        }
        token = jwt.encode(payload, "test_secret", algorithm="HS256")

        # When validating with correct issuer
        decoded = jwt.decode(
            token,
            "test_secret",
            algorithms=["HS256"],
            issuer="sergas-auth"
        )

        # Then should succeed
        assert decoded["iss"] == "sergas-auth"

    def test_token_algorithm_validation(self, valid_access_token):
        """Test JWT algorithm validation (prevent 'none' algorithm)."""
        # Given token with HS256
        # When attempting to decode with 'none' algorithm
        # Then should be rejected
        with pytest.raises((jwt.DecodeError, jwt.InvalidAlgorithmError)):
            jwt.decode(valid_access_token, None, algorithms=["none"])

    def test_token_claims_validation(self, valid_access_token):
        """Test required JWT claims are present."""
        # Given valid token
        decoded = jwt.decode(
            valid_access_token,
            "test_secret",
            algorithms=["HS256"]
        )

        # Then should have required claims
        assert "sub" in decoded
        assert "exp" in decoded
        assert "iat" in decoded

    def test_token_entropy_validation(self):
        """Test token has sufficient entropy."""
        # Given generated token
        token = secrets.token_urlsafe(32)

        # Then should have sufficient length
        assert len(token) >= 32

        # And should be unique across generations
        token2 = secrets.token_urlsafe(32)
        assert token != token2

    def test_token_format_validation(self):
        """Test JWT format validation."""
        # Given malformed JWT
        malformed_tokens = [
            "not.a.jwt",
            "only.two.parts",
            "",
            "a" * 1000,
        ]

        # When validating format
        # Then should raise decode error
        for malformed in malformed_tokens:
            with pytest.raises((jwt.DecodeError, jwt.InvalidTokenError)):
                jwt.decode(malformed, "test_secret", algorithms=["HS256"])


# =================================================================
# Session Security Tests (8 tests)
# =================================================================

class TestSessionSecurity:
    """Test session management security."""

    def test_session_token_generation(self):
        """Test secure session token generation."""
        # Given session token generator
        # When generating token
        token = secrets.token_urlsafe(64)

        # Then should have sufficient entropy (>= 128 bits)
        assert len(token) >= 64

    def test_session_token_uniqueness(self):
        """Test session tokens are unique."""
        # Given multiple token generations
        tokens = [secrets.token_urlsafe(64) for _ in range(100)]

        # Then all should be unique
        assert len(tokens) == len(set(tokens))

    def test_session_timeout_enforcement(self):
        """Test session idle timeout enforcement."""
        # Given session with last activity time
        session = {
            "token": "test_session",
            "last_activity": datetime.utcnow() - timedelta(minutes=20),
            "idle_timeout_minutes": 15
        }

        # When checking if session is expired
        is_expired = self._is_session_expired(session)

        # Then should be expired
        assert is_expired is True

    def test_session_absolute_timeout(self):
        """Test session absolute timeout enforcement."""
        # Given session created long ago
        session = {
            "token": "test_session",
            "created_at": datetime.utcnow() - timedelta(hours=9),
            "absolute_timeout_hours": 8,
            "last_activity": datetime.utcnow()  # Recent activity
        }

        # When checking absolute timeout
        is_expired = self._is_session_absolute_expired(session)

        # Then should be expired despite recent activity
        assert is_expired is True

    def test_session_regeneration_on_privilege_change(self):
        """Test session token regeneration on privilege escalation."""
        # Given user session
        old_token = "old_session_token"
        session = {
            "token": old_token,
            "user_id": "user123",
            "role": "user"
        }

        # When user role changes to admin
        new_session = self._regenerate_session_on_privilege_change(
            session,
            new_role="admin"
        )

        # Then session token should be regenerated
        assert new_session["token"] != old_token
        assert new_session["role"] == "admin"

    def test_session_ip_binding(self):
        """Test session binding to IP address."""
        # Given session bound to IP
        session = {
            "token": "test_session",
            "ip_address": "192.168.1.100"
        }

        # When validating from same IP
        is_valid = self._validate_session_ip(session, "192.168.1.100")
        assert is_valid is True

        # When validating from different IP
        is_valid = self._validate_session_ip(session, "10.0.0.1")
        assert is_valid is False

    def test_session_user_agent_binding(self):
        """Test session binding to user agent."""
        # Given session bound to user agent
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        session = {
            "token": "test_session",
            "user_agent": user_agent
        }

        # When validating with same user agent
        is_valid = self._validate_session_user_agent(session, user_agent)
        assert is_valid is True

        # When validating with different user agent
        different_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)"
        is_valid = self._validate_session_user_agent(session, different_ua)
        assert is_valid is False

    def test_session_concurrent_session_limit(self):
        """Test enforcement of concurrent session limit."""
        # Given user with multiple sessions
        user_sessions = [
            {"token": f"session_{i}", "user_id": "user123"}
            for i in range(5)
        ]

        # When enforcing limit of 3 concurrent sessions
        max_sessions = 3
        active_sessions = self._enforce_session_limit(
            user_sessions,
            max_sessions
        )

        # Then should keep only newest sessions
        assert len(active_sessions) == max_sessions


# =================================================================
# Permission Enforcement Tests (7 tests)
# =================================================================

class TestPermissionEnforcement:
    """Test role-based access control and permission enforcement."""

    def test_rbac_role_assignment(self):
        """Test role assignment to users."""
        # Given user without role
        user = {"id": "user123", "roles": []}

        # When assigning role
        user["roles"].append("account_owner")

        # Then user should have role
        assert "account_owner" in user["roles"]

    def test_rbac_permission_check(self):
        """Test permission checking based on roles."""
        # Given user with role
        user = {"id": "user123", "roles": ["account_owner"]}

        # And role permissions
        role_permissions = {
            "account_owner": [
                "accounts:read",
                "accounts:update_assigned",
                "recommendations:approve"
            ]
        }

        # When checking permission
        has_permission = self._check_permission(
            user,
            "accounts:read",
            role_permissions
        )

        # Then should have permission
        assert has_permission is True

    def test_rbac_permission_denied(self):
        """Test permission denial for unauthorized actions."""
        # Given user with limited role
        user = {"id": "user123", "roles": ["analyst"]}

        # And role permissions
        role_permissions = {
            "analyst": ["accounts:read", "recommendations:read"]
        }

        # When checking admin permission
        has_permission = self._check_permission(
            user,
            "users:delete",
            role_permissions
        )

        # Then should deny permission
        assert has_permission is False

    def test_rbac_multiple_roles(self):
        """Test permission checking with multiple roles."""
        # Given user with multiple roles
        user = {"id": "user123", "roles": ["analyst", "auditor"]}

        # And role permissions
        role_permissions = {
            "analyst": ["accounts:read"],
            "auditor": ["audit:read"]
        }

        # When checking permissions from both roles
        has_analyst_perm = self._check_permission(
            user,
            "accounts:read",
            role_permissions
        )
        has_auditor_perm = self._check_permission(
            user,
            "audit:read",
            role_permissions
        )

        # Then should have both permissions
        assert has_analyst_perm is True
        assert has_auditor_perm is True

    def test_rbac_role_hierarchy(self):
        """Test role hierarchy (admin inherits all permissions)."""
        # Given admin user
        user = {"id": "admin123", "roles": ["admin"]}

        # When checking any permission
        permissions_to_check = [
            "users:delete",
            "accounts:read",
            "system:configure",
            "audit:read"
        ]

        # Then admin should have all permissions
        for permission in permissions_to_check:
            has_permission = self._check_admin_permission(user, permission)
            assert has_permission is True

    def test_rbac_resource_ownership(self):
        """Test resource-based permission checking."""
        # Given user can only access their own accounts
        user = {"id": "user123", "roles": ["account_owner"]}
        user_accounts = ["account1", "account2"]

        # When checking access to owned account
        can_access = self._check_resource_access(
            user,
            "account1",
            user_accounts
        )
        assert can_access is True

        # When checking access to non-owned account
        can_access = self._check_resource_access(
            user,
            "account999",
            user_accounts
        )
        assert can_access is False

    def test_rbac_segregation_of_duties(self):
        """Test segregation of duties (conflicting roles)."""
        # Given conflicting role pairs
        conflicting_roles = [
            ("admin", "auditor"),
            ("account_owner", "auditor")
        ]

        # When assigning conflicting roles
        user = {"id": "user123", "roles": ["admin"]}

        # Then should prevent assignment of auditor role
        can_assign = self._can_assign_role(
            user["roles"],
            "auditor",
            conflicting_roles
        )
        assert can_assign is False


# =================================================================
# Helper Methods
# =================================================================

def _generate_auth_url(config: ZohoSDKConfig, state: Optional[str] = None) -> str:
    """Generate OAuth authorization URL."""
    base_url = "https://accounts.zoho.com/oauth/v2/auth"
    params = {
        "client_id": config.client_id,
        "redirect_uri": config.redirect_url,
        "response_type": "code",
        "scope": "ZohoCRM.modules.ALL",
        "access_type": "offline"
    }
    if state:
        params["state"] = state

    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base_url}?{query_string}"


def _generate_auth_url_with_pkce(
    config: ZohoSDKConfig,
    code_challenge: str
) -> str:
    """Generate OAuth URL with PKCE."""
    base_url = _generate_auth_url(config)
    return f"{base_url}&code_challenge={code_challenge}&code_challenge_method=S256"


def _exchange_code_for_token(config: ZohoSDKConfig, code: str) -> Dict[str, Any]:
    """Exchange authorization code for access token."""
    import requests
    response = requests.post("https://accounts.zoho.com/oauth/v2/token", data={
        "client_id": config.client_id,
        "client_secret": config.client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": config.redirect_url
    })
    if response.status_code != 200:
        error = response.json().get("error")
        raise ZohoAuthError(f"Token exchange failed: {error}")
    return response.json()


def _refresh_access_token(config: ZohoSDKConfig, refresh_token: str) -> Dict[str, Any]:
    """Refresh access token."""
    import requests
    response = requests.post("https://accounts.zoho.com/oauth/v2/token", data={
        "client_id": config.client_id,
        "client_secret": config.client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    })
    return response.json()


def _revoke_token(config: ZohoSDKConfig, token: str) -> bool:
    """Revoke OAuth token."""
    import requests
    response = requests.post("https://accounts.zoho.com/oauth/v2/token/revoke", data={
        "token": token
    })
    return response.status_code == 200


def _validate_redirect_uri(redirect_uri: str, config: ZohoSDKConfig) -> bool:
    """Validate redirect URI matches configuration."""
    return redirect_uri == config.redirect_url


def _is_session_expired(session: Dict[str, Any]) -> bool:
    """Check if session has expired (idle timeout)."""
    last_activity = session["last_activity"]
    idle_timeout = timedelta(minutes=session["idle_timeout_minutes"])
    return datetime.utcnow() > (last_activity + idle_timeout)


def _is_session_absolute_expired(session: Dict[str, Any]) -> bool:
    """Check if session has reached absolute timeout."""
    created_at = session["created_at"]
    absolute_timeout = timedelta(hours=session["absolute_timeout_hours"])
    return datetime.utcnow() > (created_at + absolute_timeout)


def _regenerate_session_on_privilege_change(
    session: Dict[str, Any],
    new_role: str
) -> Dict[str, Any]:
    """Regenerate session token on privilege change."""
    new_session = session.copy()
    new_session["token"] = secrets.token_urlsafe(64)
    new_session["role"] = new_role
    return new_session


def _validate_session_ip(session: Dict[str, Any], current_ip: str) -> bool:
    """Validate session IP binding."""
    return session["ip_address"] == current_ip


def _validate_session_user_agent(session: Dict[str, Any], current_ua: str) -> bool:
    """Validate session user agent binding."""
    return session["user_agent"] == current_ua


def _enforce_session_limit(sessions: list, max_sessions: int) -> list:
    """Enforce concurrent session limit."""
    return sessions[-max_sessions:]


def _check_permission(
    user: Dict[str, Any],
    permission: str,
    role_permissions: Dict[str, list]
) -> bool:
    """Check if user has permission based on roles."""
    for role in user.get("roles", []):
        if permission in role_permissions.get(role, []):
            return True
    return False


def _check_admin_permission(user: Dict[str, Any], permission: str) -> bool:
    """Check admin has all permissions."""
    return "admin" in user.get("roles", [])


def _check_resource_access(
    user: Dict[str, Any],
    resource_id: str,
    user_resources: list
) -> bool:
    """Check resource-based access."""
    return resource_id in user_resources


def _can_assign_role(
    current_roles: list,
    new_role: str,
    conflicting_roles: list
) -> bool:
    """Check if role can be assigned (segregation of duties)."""
    for role1, role2 in conflicting_roles:
        if role1 in current_roles and new_role == role2:
            return False
        if role2 in current_roles and new_role == role1:
            return False
    return True
