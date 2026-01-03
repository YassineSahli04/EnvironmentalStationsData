from datetime import datetime, timezone
from zoneinfo import ZoneInfo

class DateTimeHelper:


    @staticmethod
    def to_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None

        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            TUNIS = ZoneInfo("Africa/Tunis")
            dt = dt.replace(tzinfo=TUNIS)

        return dt.astimezone(timezone.utc)