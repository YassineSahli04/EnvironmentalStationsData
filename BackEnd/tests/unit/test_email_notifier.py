from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from BackEnd.Utils.EmailNotifier import EmailNotifier
from BackEnd.PostgreSQL.StationDbObject import StationState


def _make_station(state: StationState, name="TestStation", station_id=1):
    station = MagicMock()
    station.Id = station_id
    station.Name = name
    station.Location = "Tunis"
    station.Manufacturer = "Pessl"
    station.State = state
    station.Latitude = 36.8
    station.Longitude = 10.18
    station.LastDataPointTime = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    return station


class TestCreateStateChangeEmailContent:
    def test_online_station(self):
        notifier = EmailNotifier(["a@b.com"])
        station = _make_station(StationState.Online)
        subject, body = notifier._create_state_change_email_content(station)

        assert "ONLINE" in subject
        assert "TestStation" in subject
        assert "Online" in body
        assert "Tunis" in body

    def test_offline_station(self):
        notifier = EmailNotifier(["a@b.com"])
        station = _make_station(StationState.Offline)
        subject, body = notifier._create_state_change_email_content(station)

        assert "OFFLINE" in subject
        assert "Offline" in body


class TestSendEmail:
    def test_no_valid_recipients_skips(self):
        notifier = EmailNotifier([])
        notifier._send_email("subj", "body")
        # no exception; coverage for the early-return branch

    def test_whitespace_only_recipients_skips(self):
        notifier = EmailNotifier(["  ", ""])
        notifier._send_email("subj", "body")

    @patch("BackEnd.Utils.EmailNotifier.smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        notifier = EmailNotifier(["user@example.com"])
        notifier._send_email("Test Subject", "Test Body")

        mock_server.sendmail.assert_called_once()


class TestSendStationStateChangeEmail:
    @patch("BackEnd.Utils.EmailNotifier.smtplib.SMTP")
    def test_delegates_to_send_email(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        station = _make_station(StationState.Offline)
        notifier = EmailNotifier(["admin@example.com"])
        notifier.send_station_state_change_email(station)

        mock_server.sendmail.assert_called_once()
