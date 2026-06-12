# models.py
from pydantic import BaseModel
from typing import Dict, Any

class Event(BaseModel):
    service: str
    status: str
    payload: Dict[str, Any]

class Target(BaseModel):
    service: str
    action: str

class Call(BaseModel):
    caller: str
    target: Target

class Reply(BaseModel):
    service: str
    reply_to: str
    status: str
    payload: Dict[str, Any]
