from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from BackEnd.PostgreSQL.User import UserSerializable, UserRole


def _user_serializable(uid="1"):
    return UserSerializable(
        Id=uid,
        FirstName="Alice",
        LastName="Smith",
        Email="alice@example.com",
        Role="admin",
        CreatedAt=datetime(2025, 1, 1, tzinfo=timezone.utc),
        IsSubscribedToStationAlerts=True,
        TypeFilter=["Meteorological"],
    )


class TestSyncUser:
    def test_200(self, client, mock_auth_admin, admin_user):
        admin_user.ClerkId = "clerk_test_id"
        admin_user.Role = UserRole.Admin
        admin_user.TypeFilter = ["Meteorological"]

        resp = client.post("/api/users/sync")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "clerk_test_id"
        assert body["role"] == "admin"

    def test_401_without_auth(self, client, mock_auth_none):
        resp = client.post("/api/users/sync")
        assert resp.status_code == 401


class TestGetAllUsers:
    @patch("BackEnd.app.user_routes.db")
    def test_200_admin(self, mock_db, client, mock_auth_admin):
        mock_user = MagicMock()
        mock_user.getSerializableUser.return_value = _user_serializable()
        mock_db.get_all_user_objects.return_value = [mock_user]

        resp = client.get("/api/users/all")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @patch("BackEnd.app.user_routes.db")
    def test_403_without_admin(self, mock_db, client, mock_auth_user):
        resp = client.get("/api/users/all")
        assert resp.status_code == 403


class TestUpdateUser:
    @patch("BackEnd.app.user_routes.User")
    def test_200(self, MockUser, client, mock_auth_admin):
        mock_instance = MagicMock()
        mock_instance.getSerializableUser.return_value = _user_serializable()
        MockUser.from_id.return_value = mock_instance

        resp = client.patch(
            "/api/users/update/1",
            json={"IsSubscribedToStationAlerts": False, "Role": "user"},
        )
        assert resp.status_code == 200
        mock_instance.updateUser.assert_called_once_with(False, "user")

    @patch("BackEnd.app.user_routes.User")
    def test_404_when_not_found(self, MockUser, client, mock_auth_admin):
        MockUser.from_id.side_effect = ValueError("User not found")

        resp = client.patch(
            "/api/users/update/999",
            json={"Role": "admin"},
        )
        assert resp.status_code == 404
