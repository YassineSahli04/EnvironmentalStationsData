"""Integration test fixtures – TestClient and auth helpers."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from BackEnd.app.main import app
from BackEnd.PostgreSQL.User import User, UserRole


@pytest.fixture()
def client():
    return TestClient(app, raise_server_exceptions=False)


def _make_user(role: UserRole, type_filter: list[str] | None = None) -> MagicMock:
    user = MagicMock(spec=User)
    user.Id = "1"
    user.ClerkId = "clerk_test_id"
    user.FirstName = "Test"
    user.LastName = "User"
    user.Email = "test@example.com"
    user.Role = role
    user.TypeFilter = type_filter or [
        "Meteorological",
        "Pyranometer",
        "Pluviometer",
        "Meteorological/Pluviometer",
    ]
    user.IsSubscribedToStationAlerts = False
    return user


@pytest.fixture()
def admin_user():
    return _make_user(UserRole.Admin)


@pytest.fixture()
def regular_user():
    return _make_user(UserRole.User)


@pytest.fixture()
def mock_auth_admin(admin_user):
    """Patch clerk_auth in the auth module to authenticate as admin."""
    rs = MagicMock()
    rs.is_signed_in = True
    rs.payload = {"sub": "clerk_test_id"}

    with (
        patch("BackEnd.app.auth.clerk_auth") as auth_clerk,
        patch("BackEnd.app.user_routes.clerk_auth") as user_clerk,
    ):
        for m in (auth_clerk, user_clerk):
            m.authenticate.return_value = rs
            m.getClerkUser.return_value = admin_user
            m.get_or_create_user.return_value = None
        yield auth_clerk


@pytest.fixture()
def mock_auth_user(regular_user):
    """Patch clerk_auth to authenticate as a regular (non-admin) user."""
    rs = MagicMock()
    rs.is_signed_in = True
    rs.payload = {"sub": "clerk_test_id"}

    with (
        patch("BackEnd.app.auth.clerk_auth") as auth_clerk,
        patch("BackEnd.app.user_routes.clerk_auth") as user_clerk,
    ):
        for m in (auth_clerk, user_clerk):
            m.authenticate.return_value = rs
            m.getClerkUser.return_value = regular_user
            m.get_or_create_user.return_value = None
        yield auth_clerk


@pytest.fixture()
def mock_auth_none():
    """Patch clerk_auth so that authentication fails (returns None)."""
    with (
        patch("BackEnd.app.auth.clerk_auth") as auth_clerk,
        patch("BackEnd.app.user_routes.clerk_auth") as user_clerk,
    ):
        for m in (auth_clerk, user_clerk):
            m.authenticate.return_value = None
        yield auth_clerk
