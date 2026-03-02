from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Optional, List, TypedDict
from langgraph.graph import add_messages
from pydantic import BaseModel


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
    output_kind: Optional[str]

    is_data_request: bool
    data_validation_status: Optional[str]
    data_entry_model_resolve_attempted: bool
    data_validation_request_model_issues: Optional[list[dict]]
    data_validation_failed_issues: Optional[list[dict]]


class IntentResult(BaseModel):
    is_data_request: bool


class ExtractedRequestResult(BaseModel):
    variables_selected: Optional[list[str]] = None
    dataGroup: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    output_kind: Optional[str] = None
