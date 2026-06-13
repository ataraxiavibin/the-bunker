# bunker.py

import os
import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv
from loguru import logger

from shared.models import Event, Call, Reply, Target

logger.add("./logs/bunker.log", rotation="10 MB", retention="30 days", level="INFO")

app = FastAPI()

load_dotenv()
api_token = os.environ.get("API_TOKEN")
agent_url = os.environ.get("AGENT_URL")


@app.post("/event")
async def handle_event(event: Event, request: Request, x_token: str = Header(...)):
    if x_token != api_token:
        logger.warning(f"Failed auth attempt from {request.client.host}")
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info(f"Event from {event.service}: STATUS - {event.status} | PAYLOAD - {event.payload}")

    return {"status": "accepted"}

@app.get("/ping")
async def handle_ping():
    return {"status": "alive"}

@app.post("/call")
async def forward_call(call: Call, request: Request, x_token: str = Header(...)) -> Dict[str, Any]:
    if x_token != api_token:
        logger.warning(f"Failed auth attempt from {request.client.host}")
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info(f"Call from {call.caller} to {call.target.service}: ACTION - {call.target.action}")

    headers = {"x-token": api_token}
    data = {
        "caller": call.caller,
        "target": call.target.model_dump()
    }

    try:
        async with httpx.AsyncClient() as client:
            result = await client.post(
                f"{agent_url}/call",
                json=data,
                headers=headers,
                timeout=20.0
            )

        result.raise_for_status()
        agent_data = result.json()
        
    except httpx.TimeoutException as e:
        logger.warning(f"Request timed out: {e}")
        raise HTTPException(status_code=504, detail="Agent did not reply in time")
    except httpx.HTTPError as e:
        logger.warning(f"Couldn't reach agent.py: {e}")
        raise HTTPException(status_code=502, detail="Agent is unreachable")
    except Exception as e:
        logger.warning(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Error")

    try:
        status = agent_data["status"]
        payload = agent_data["payload"]["stdout"]["payload"] # yeah this is complicated.
    except (KeyError, TypeError) as e:
        logger.error(f"Something is wrong with the payload: {agent_data} | {e}")
        raise HTTPException(status_code=400, detail="Something went wrong on agent/service side. Check logs/bunker.log")

    logger.info(f"Got back reply: {agent_data}")
    logger.info(f"Sent back payload to {call.caller}: {payload}")
    if status == "fatal":
        reason = payload.get("reason", "Unknown agent error")
        raise HTTPException(status_code=400, detail=reason)

    return payload


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)
