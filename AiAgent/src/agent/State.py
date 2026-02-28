from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Dict, Optional, List, TypedDict
from langgraph.graph import add_messages


@dataclass
class TimeRange:
    start: Optional[str]
    end: Optional[str]


class State(TypedDict):
    messages: Annotated[list, add_messages]

    station_id: Optional[str]
    station_meta: Optional[dict]
    station_meta: Optional[dict]

    time_range: TimeRange
    variables_selected: List[str]
    dataGroup: Optional[str]

    data_validation_status: Optional[str]
    data_entry_model_resolve_attempted: bool
    data_validation_request_model_issues: Optional[list[dict]]
    data_validation_failed_issues: Optional[list[dict]]


