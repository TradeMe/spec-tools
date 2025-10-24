"""Tests for authentication system."""

import pytest


class MockAuthSystem:
    """Mock authentication system for testing."""

    def __init__(self):
        self.users = {}
        self.failed_attempts = {}
        self.locked_accounts = set()
        self.sessions = {}

    def register(self, email, password):
        """Register a new user."""
        if email in self.users:
            raise ValueError("Email already registered")
        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters")
        self.users[email] = self._hash_password(password)
        return True

    def login(self, email, password):
        """Log in a user."""
        if email in self.locked_accounts:
            raise ValueError("Account locked")
        if email not in self.users:
            self._increment_failed_attempts(email)
            raise ValueError("Invalid credentials")
        if not self._verify_password(password, self.users[email]):
            self._increment_failed_attempts(email)
            raise ValueError("Invalid credentials")
        # Reset failed attempts on successful login
        self.failed_attempts[email] = 0
        return self._create_session(email)

    def logout(self, session_token):
        """Log out a user."""
        if session_token in self.sessions:
            del self.sessions[session_token]

    def _hash_password(self, password):
        """Hash a password."""
        # Simplified for testing
        return f"hashed_{password}"

    def _verify_password(self, password, hashed):
        """Verify a password."""
        return f"hashed_{password}" == hashed

    def _increment_failed_attempts(self, email):
        """Increment failed login attempts."""
        self.failed_attempts[email] = self.failed_attempts.get(email, 0) + 1
        if self.failed_attempts[email] >= 5:
            self.locked_accounts.add(email)

    def _create_session(self, email):
        """Create a session token."""
        import secrets

        token = secrets.token_hex(32)  # 256 bits
        self.sessions[token] = email
        return token


class TestUserRegistration:
    """Test suite for user registration."""

    @pytest.mark.req("SPEC-200/REQ-001")
    def test_user_can_register_with_email_and_password(self):
        """Test that users can register with email and password."""
        auth = MockAuthSystem()
        result = auth.register("user@example.com", "securepassword123")
        assert result is True
        assert "user@example.com" in auth.users

    @pytest.mark.req("SPEC-200/REQ-003")
    def test_duplicate_email_registration_rejected(self):
        """Test that duplicate email registration is rejected."""
        auth = MockAuthSystem()
        auth.register("user@example.com", "securepassword123")

        with pytest.raises(ValueError, match="Email already registered"):
            auth.register("user@example.com", "anotherpassword123")

    @pytest.mark.req("SPEC-200/REQ-004")
    def test_password_length_requirement(self):
        """Test that passwords must be at least 12 characters."""
        auth = MockAuthSystem()

        with pytest.raises(ValueError, match="at least 12 characters"):
            auth.register("user@example.com", "short")

        # Valid password should work
        result = auth.register("user@example.com", "longenoughpassword")
        assert result is True


class TestUserLogin:
    """Test suite for user login."""

    @pytest.mark.req("SPEC-200/REQ-005")
    def test_registered_user_can_login(self):
        """Test that registered users can log in."""
        auth = MockAuthSystem()
        auth.register("user@example.com", "securepassword123")

        session_token = auth.login("user@example.com", "securepassword123")
        assert session_token is not None
        assert session_token in auth.sessions

    @pytest.mark.req("SPEC-200/REQ-007")
    def test_failed_login_increments_counter(self):
        """Test that failed logins increment the counter."""
        auth = MockAuthSystem()
        auth.register("user@example.com", "securepassword123")

        # Attempt login with wrong password
        with pytest.raises(ValueError):
            auth.login("user@example.com", "wrongpassword")

        assert auth.failed_attempts.get("user@example.com", 0) == 1

    @pytest.mark.req("SPEC-200/REQ-008")
    def test_account_lockout_after_five_failures(self):
        """Test that accounts are locked after 5 failed attempts."""
        auth = MockAuthSystem()
        auth.register("user@example.com", "securepassword123")

        # Make 5 failed login attempts
        for _ in range(5):
            with pytest.raises(ValueError):
                auth.login("user@example.com", "wrongpassword")

        # Account should be locked
        assert "user@example.com" in auth.locked_accounts

        # Even correct password should not work
        with pytest.raises(ValueError, match="Account locked"):
            auth.login("user@example.com", "securepassword123")


class TestSessionManagement:
    """Test suite for session management."""

    @pytest.mark.req("SPEC-200/REQ-009")
    def test_session_token_created_on_login(self):
        """Test that a session token is created upon login."""
        auth = MockAuthSystem()
        auth.register("user@example.com", "securepassword123")

        session_token = auth.login("user@example.com", "securepassword123")

        assert session_token is not None
        assert len(session_token) == 64  # 32 bytes = 64 hex chars

    @pytest.mark.req("SPEC-200/REQ-011")
    def test_logout_invalidates_session(self):
        """Test that logout invalidates the session token."""
        auth = MockAuthSystem()
        auth.register("user@example.com", "securepassword123")
        session_token = auth.login("user@example.com", "securepassword123")

        auth.logout(session_token)

        assert session_token not in auth.sessions


class TestSecurity:
    """Test suite for security requirements."""

    @pytest.mark.req("SPEC-200/NFR-003")
    def test_session_tokens_are_cryptographically_secure(self):
        """Test that session tokens are cryptographically secure."""
        auth = MockAuthSystem()
        auth.register("user@example.com", "securepassword123")

        # Create multiple sessions and verify uniqueness
        tokens = set()
        for _ in range(100):
            auth.register(f"user{_}@example.com", "securepassword123")
            token = auth.login(f"user{_}@example.com", "securepassword123")
            tokens.add(token)

        # All tokens should be unique
        assert len(tokens) == 100

    @pytest.mark.req("SPEC-200/TEST-001")
    def test_fixture_for_creating_test_users(self):
        """Test that test fixtures can create authenticated users."""
        auth = MockAuthSystem()
        # This simulates a test fixture
        auth.register("test@example.com", "testpassword123")
        session = auth.login("test@example.com", "testpassword123")

        assert session is not None
        assert "test@example.com" in auth.users


# Note: Some requirements are intentionally not tested to simulate partial coverage:
# - SPEC-200/REQ-002 (Email validation)
# - SPEC-200/REQ-006 (Password verification)
# - SPEC-200/REQ-010 (Session expiration)
# - SPEC-200/NFR-001 (bcrypt hashing)
# - SPEC-200/NFR-002 (HTTPS requirement - infrastructure level)
