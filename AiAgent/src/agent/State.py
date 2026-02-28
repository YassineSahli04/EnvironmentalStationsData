from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any, Optional, List, Dict, TypedDict
from langgraph.graph import add_messages


@dataclass
class TimeRange:
    start: Optional[str]
    end: Optional[str]


class State(TypedDict):
    messages: Annotated[list, add_messages]

    station_id: Optional[str]
    station_meta: Optional[dict]

    time_range: TimeRange
    variables_selected: List[str]
    dataGroup: Optional[str]


