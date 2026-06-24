# models.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Literal, Union, Annotated, Optional
from datetime import datetime

# -------
# Event
# -------

class EventBase(BaseModel):
    service: str
    action: str
    stderr: str
    timestamp: datetime
    duration_ms: int

class EventOk(EventBase):
    status: Literal["ok"] = "ok"
    payload: Dict[str, Any]

class EventError(EventBase):
    status: Literal["error", "fatal"] = "error"
    returncode: int
    reason: Optional[str]
    payload: Optional[Dict[str, Any]]


# discriminate by status, because it's the common field
Event = Annotated[Union[EventOk, EventError], Field(discriminator="status")]


# -------
# Call
# -------

class Call(BaseModel):
    caller: str
    target: Target

class Target(BaseModel):
    service: str
    action: Optional[str] = None

# -------
# Reply
# -------

class ReplyBase(BaseModel):
    service: str
    action: str
    stderr: str
    reply_to: str
    timestamp: datetime
    duration_ms: int

class ReplyOk(ReplyBase):
    status: Literal["ok"] = "ok"
    payload: Dict[str, Any]

class ReplyError(ReplyBase):
    status: Literal["error", "fatal"] = "error"
    returncode: int
    reason: Optional[str]
    payload: Optional[Dict[str, Any]]

Reply = Annotated[Union[ReplyOk, ReplyError], Field(discriminator="status")]
