from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone

from BackEnd.PostgreSQL.User import User, UserRole, UserSerializable


def _mock_engine_with_row(row_mapping):
    """Return a mock engine whose connection.execute returns *row_mapping*."""
    engine = MagicMock()
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = row_mapping
    engine.connect.return_value.__enter__ = MagicMock(return_value=MagicMock(
        execute=MagicMock(return_value=mock_result)
    ))
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    return engine


SAMPLE_ROW = {
    "id": "42",
    "clerk_user_id": "clk_abc",
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice@example.com",
    "role": "admin",
    "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
    "issubscribedtostationalerts": True,
    "type_filter": ["Meteorological"],
}


class TestGuestUser:
    def test_returns_guest_role(self):
        guest = User.getGuestUser(MagicMock())
        assert guest.Role == UserRole.Guest

    def test_has_default_type_filter(self):
        guest = User.getGuestUser(MagicMock())
        assert "Meteorological" in guest.TypeFilter
        assert "Pyranometer" in guest.TypeFilter
        assert len(guest.TypeFilter) == 4

    def test_clerk_id_set(self):
        guest = User.getGuestUser(MagicMock())
        assert guest.ClerkId == "guestClerkId"


class TestFromId:
    def test_populates_attributes(self):
        engine = _mock_engine_with_row(SAMPLE_ROW)
        user = User.from_id(engine, "42")

        assert user.Id == "42"
        assert user.ClerkId == "clk_abc"
        assert user.FirstName == "Alice"
        assert user.Role == UserRole.Admin
        assert user.Email == "alice@example.com"
        assert user.IsSubscribedToStationAlerts is True
        assert user.TypeFilter == ["Meteorological"]

    def test_no_row_leaves_attrs_unset(self):
        engine = _mock_engine_with_row(None)
        user = User.from_id(engine, "999")
        assert not hasattr(user, "Id")


class TestFromClerkId:
    def test_populates_attributes(self):
        engine = _mock_engine_with_row(SAMPLE_ROW)
        user = User.from_clerk_id(engine, "clk_abc")
        assert user.Role == UserRole.Admin


class TestSerializableUser:
    def test_all_fields_mapped(self):
        engine = _mock_engine_with_row(SAMPLE_ROW)
        user = User.from_id(engine, "42")
        s = user.getSerializableUser()

        assert isinstance(s, UserSerializable)
        assert s.Id == "42"
        assert s.FirstName == "Alice"
        assert s.Role == "admin"
        assert s.IsSubscribedToStationAlerts is True


class TestUpdateUser:
    def test_updates_subscription_and_role(self):
        engine = _mock_engine_with_row(SAMPLE_ROW)
        user = User.from_id(engine, "42")

        mock_conn = MagicMock()
        engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        user.updateUser(newSubscription=False, newRole="user")

        mock_conn.execute.assert_called_once()
        assert user.IsSubscribedToStationAlerts is False
        assert user.Role == UserRole.User

    def test_no_change_skips_query(self):
        engine = _mock_engine_with_row(SAMPLE_ROW)
        user = User.from_id(engine, "42")

        mock_conn = MagicMock()
        engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        user.updateUser(newSubscription=True, newRole="admin")
        mock_conn.execute.assert_not_called()
