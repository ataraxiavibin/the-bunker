# models.py
from pydantic import BaseModel, Field, TypeAdapter
from typing import Dict, Any, Literal, Union, Annotated, Optional
from datetime import datetime

# -------
# Event
# -------

class EventBase(BaseModel):
    id: str
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
    reason: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


# discriminate by status, because it's the common field
Event = Annotated[Union[EventOk, EventError], Field(discriminator="status")]

# -------
# Intent & Call
# -------

class Intent(BaseModel):
    caller: str
    target: Target

class Call(Intent):
    id: str

class Target(BaseModel):
    service: str
    action: Optional[str] = None # this may change

# -------
# Reply
# -------

class ReplyBase(BaseModel):
    id: str
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
    reason: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

Reply = Annotated[Union[ReplyOk, ReplyError], Field(discriminator="status")]
ReplyAdapter = TypeAdapter(Reply)

# -------
# Bunker
# -------

class ProcessedReplyBase(BaseModel):
    duration_ms: int
    # id: int -> when real async EDA

class ProcessedReplyOk(ProcessedReplyBase):
    status: Literal["ok"] = "ok"
    payload: Dict[str, Any]

class ProcessedReplyWarning(ProcessedReplyBase): # not used rn
    status: Literal["warning"] = "warning"
    payload: Dict[str, Any]
    notes: Dict[str, Any]

class ProcessedReplyError(ProcessedReplyBase):
    status: Literal["error", "fatal"] = "error"
    payload: Optional[Dict[str, Any]] = None
    notes: Optional[Dict[str, Any]] = None
    reason: str

ProcessedReply = Annotated[Union[ProcessedReplyOk, ProcessedReplyError], Field(discriminator="status")]

class BunkerError(BaseModel):
    status: Literal["fatal"] = "fatal"
    reason: str

