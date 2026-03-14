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
    recheck_intent: Optional[bool]

    extracted_variables_selected: Optional[List[str]]
    extracted_dataGroup: Optional[str]
    extracted_time_phrase: Optional[str]
    extracted_start: Optional[str]
    extracted_end: Optional[str]
    extracted_output_kind: Optional[str]

    time_range: Optional[TimeRange]
    variables_selected: Optional[List[str]]
    dataGroup: Optional[str]
    output_kind: Optional[str]

    is_data_request: bool
    data_validation_status: Optional[str]

    is_data_entry_first_pass: bool
    data_validation_issues: Optional[list[dict]]


class IntentResult(BaseModel):
    is_data_request: bool


class ExtractedRequestResult(BaseModel):
    extracted_variables_selected: Optional[list[str]] = None
    extracted_dataGroup: Optional[str] = None
    extracted_time_phrase: Optional[str] = None
    extracted_start: Optional[str] = None
    extracted_end: Optional[str] = None
    extracted_output_kind: Optional[str] = None
