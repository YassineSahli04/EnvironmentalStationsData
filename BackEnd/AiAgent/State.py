from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any, Optional, List, Dict, TypedDict
from langgraph.graph import add_messages
from BackEnd.PostgreSQL.StationDbObject import StationSerializable

from BackEnd.PostgreSQL.StationDbObject import StationDataGroup


@dataclass
class TimeRange:
    start: Optional[str]
    end: Optional[str]


class State(TypedDict):
    messages: Annotated[list, add_messages]

    station_id: Optional[str]
    station_meta: Optional[StationSerializable]

    time_range: TimeRange
    variables_selected: List[str]
    dataGroup: StationDataGroup


