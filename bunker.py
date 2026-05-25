# bunker.py

import os
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv
from loguru import logger

logger.add("./logs/bunker.log", rotation="10 MB", retention="30 days", level="INFO")

app = FastAPI()

load_dotenv()
api_token = os.environ.get("API_TOKEN")

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
async def handle_event(event: Event, x_token: str = Header(...), request: Request):
    if x_token != api_token:
        logger.warning(f"Failed auth attempt from {request.client.host}")
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info(f"Event from {event.source}: STATUS - {event.status} | PAYLOAD - {event.payload}")

    return {"status": "accepted"}

@app.get("/ping")
async def handle_ping():
    return {"status": "alive"}

@app.post("/call")
async def handle_call(call: Call, x_token: str = Header(...)):
    pass # here: call agent   

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)
