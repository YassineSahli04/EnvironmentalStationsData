from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from BackEnd.Utils.DateTimeHelper import DateTimeHelper


class TestToUtc:
    def test_none_returns_none(self):
        assert DateTimeHelper.to_utc(None) is None

    def test_naive_gets_tunis_then_utc(self):
        naive = datetime(2025, 7, 15, 12, 0, 0)
        result = DateTimeHelper.to_utc(naive)

        tunis = ZoneInfo("Africa/Tunis")
        expected = naive.replace(tzinfo=tunis).astimezone(timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc

    def test_aware_non_utc_converts(self):
        paris = ZoneInfo("Europe/Paris")
        aware = datetime(2025, 1, 10, 14, 0, 0, tzinfo=paris)
        result = DateTimeHelper.to_utc(aware)

        expected = aware.astimezone(timezone.utc)
        assert result == expected
        assert result.tzinfo == timezone.utc

    def test_utc_passes_through(self):
        utc_dt = datetime(2025, 6, 1, 8, 30, 0, tzinfo=timezone.utc)
        result = DateTimeHelper.to_utc(utc_dt)
        assert result == utc_dt
        assert result.tzinfo == timezone.utc
