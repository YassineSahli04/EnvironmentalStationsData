from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Optional, List, TypedDict
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


