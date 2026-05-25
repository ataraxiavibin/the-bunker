# bunker.py

import os
import requests # it's gonna be a little bit painful to switch to a new async library..
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv
from loguru import logger

logger.add("./logs/bunker.log", rotation="10 MB", retention="30 days", level="INFO")

app = FastAPI()

load_dotenv()
api_token = os.environ.get("API_TOKEN")
agent_url = os.environ.get("AGENT_URL")

class Event(BaseModel):
    source: str
    status: str
    payload: Dict[str, Any]

class Target(BaseModel):
    service: str
    action: str

class Call(BaseModel):
    source: str
    target: Target

@app.post("/event")
async def handle_event(event: Event, request: Request, x_token: str = Header(...)):
    if x_token != api_token:
        logger.warning(f"Failed auth attempt from {request.client.host}")
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info(f"Event from {event.source}: STATUS - {event.status} | PAYLOAD - {event.payload}")

    return {"status": "accepted"}

@app.get("/ping")
async def handle_ping():
    return {"status": "alive"}

@app.post("/call")
async def forward_call(call: Call, request: Request, x_token: str = Header(...)):
    if x_token != api_token:
        logger.warning(f"Failed auth attempt from {request.client.host}")
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info(f"Call from {call.source} to {call.target.service}: ACTION - {call.target.action}")

    headers = {"x-token": api_token}
    data = {
        "source": call.source,
        "target": call.target.model_dump()
    }

    try:
        response = requests.post(agent_url+"/call", json=data, headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        logger.warning(f"Couldn't reach agent.py: {e}")
        return {"status": "error"}

    return {"status": "forwarded"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)
