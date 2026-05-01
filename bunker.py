# bunker.py

import os
from fastapi import FastAPI, Header, HTTPException
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

@app.post("/event")
async def handle_event(event: Event, x_token: str = Header(None)):
    if x_token != api_token:
        logger.warning(f"Failed auth attempt with token: {x_token}")
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info(f"Event from {event.source}: STATUS - {event.status} | PAYLOAD - {event.payload}")

    return {"status": "accepted"}

@app.get("/ping")
async def health_check():
    return {"status": "alive"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)
