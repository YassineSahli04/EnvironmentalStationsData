import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from BackEnd.app.auth import require_auth, require_role, require_type_filter
from BackEnd.PostgreSQL.User import UserRole


class TestRequireAuth:
    def test_success(self):
        mock_request = MagicMock()
        mock_rs = MagicMock()

        with patch("BackEnd.app.auth.clerk_auth") as mock_clerk:
            mock_clerk.authenticate.return_value = mock_rs
            result = require_auth(mock_request)

        assert result is mock_rs

    def test_401_when_none(self):
        mock_request = MagicMock()

        with patch("BackEnd.app.auth.clerk_auth") as mock_clerk:
            mock_clerk.authenticate.return_value = None
            with pytest.raises(HTTPException) as exc_info:
                require_auth(mock_request)

        assert exc_info.value.status_code == 401


class TestRequireRole:
    def test_admin_passes(self):
        guard = require_role(UserRole.Admin)
        mock_rs = MagicMock()
        mock_user = MagicMock()
        mock_user.Role = UserRole.Admin

        with patch("BackEnd.app.auth.clerk_auth") as mock_clerk:
            mock_clerk.getClerkUser.return_value = mock_user
            result = guard(request_state=mock_rs)

        assert result is mock_rs

    def test_user_role_forbidden(self):
        guard = require_role(UserRole.Admin)
        mock_rs = MagicMock()
        mock_user = MagicMock()
        mock_user.Role = UserRole.User

        with patch("BackEnd.app.auth.clerk_auth") as mock_clerk:
            mock_clerk.getClerkUser.return_value = mock_user
            with pytest.raises(HTTPException) as exc_info:
                guard(request_state=mock_rs)

        assert exc_info.value.status_code == 403

    def test_multiple_roles_allowed(self):
        guard = require_role(UserRole.Admin, UserRole.User)
        mock_rs = MagicMock()
        mock_user = MagicMock()
        mock_user.Role = UserRole.User

        with patch("BackEnd.app.auth.clerk_auth") as mock_clerk:
            mock_clerk.getClerkUser.return_value = mock_user
            result = guard(request_state=mock_rs)

        assert result is mock_rs


class TestRequireTypeFilter:
    def test_passes_when_subset(self):
        guard = require_type_filter()
        mock_rs = MagicMock()
        mock_user = MagicMock()
        mock_user.TypeFilter = ["Meteorological", "Pyranometer"]

        with patch("BackEnd.app.auth.clerk_auth") as mock_clerk:
            mock_clerk.getClerkUser.return_value = mock_user
            guard(request_state=mock_rs, typeFilter=["Meteorological"])

    def test_403_disallowed_type(self):
        guard = require_type_filter()
        mock_rs = MagicMock()
        mock_user = MagicMock()
        mock_user.TypeFilter = ["Meteorological"]

        with patch("BackEnd.app.auth.clerk_auth") as mock_clerk:
            mock_clerk.getClerkUser.return_value = mock_user
            with pytest.raises(HTTPException) as exc_info:
                guard(request_state=mock_rs, typeFilter=["Pyranometer"])

        assert exc_info.value.status_code == 403

    def test_403_empty_filter(self):
        guard = require_type_filter()
        mock_rs = MagicMock()
        mock_user = MagicMock()
        mock_user.TypeFilter = ["Meteorological"]

        with patch("BackEnd.app.auth.clerk_auth") as mock_clerk:
            mock_clerk.getClerkUser.return_value = mock_user
            with pytest.raises(HTTPException) as exc_info:
                guard(request_state=mock_rs, typeFilter=[])

        assert exc_info.value.status_code == 403
