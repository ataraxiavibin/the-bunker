# bunker.py

import os
import httpx
import secrets
from fastapi import FastAPI, Header, HTTPException, Request, Depends
from typing import Dict, Any, Union
from dotenv import load_dotenv
from loguru import logger
from pydantic import ValidationError

from shared.models import Event, Call, Target, Intent, Reply, ReplyOk, ProcessedReplyOk, ProcessedReplyError, ProcessedReply, ReplyAdapter, BunkerError
from shared.logger import setup_logger, set_req_id
from shared.auth import verify_token

logger = setup_logger("bunker", "./logs/bunker.log")

app = FastAPI()

load_dotenv()
api_token = os.environ.get("API_TOKEN")
agent_url = os.environ.get("AGENT_URL")

# log everything, scrape anything not in ProcessedReply
async def process_reply(reply: Reply) -> ProcessedReply:
    logger.info(f"^_> processing reply: {reply.status}")
    logger.debug(f"~~ reply dump: {reply}")

    # here db logic; a new func call
    # if reply.status == "fatal": notes = ...

    if isinstance(reply, ReplyOk):
        processed = ProcessedReplyOk(
            duration_ms=reply.duration_ms,
            payload=reply.payload
        )
    else: # ReplyError
        processed = ProcessedReplyError(
            status=reply.status,
            duration_ms=reply.duration_ms,
            reason=reply.reason or "service died mid-process.", # let's see how accurate this is, should be pretty accurate and never false
            payload=reply.payload
        )

    return processed

@app.post("/event", dependencies=[Depends(verify_token)])
async def handle_event(event: Event) -> Dict[str, str]:
    set_req_id(event.id)

    logger.info(f"~~ event received: {event.service} finished with status {event.status}")
    logger.debug(f"~~ payload: {event.payload}")

    return {"status": "accepted"}

@app.get("/ping")
async def ping():
    logger.debug("~~ received ping.")
    return {"status": "alive"}

@app.post("/register", dependencies=[Depends(verify_token)])
async def register(intent: Union[Intent, Target]) -> Dict[str, str]:
    # generate a request id
    req_id = secrets.token_hex(3)

    # set contextvar of this request
    set_req_id(req_id)

    # extract the info
    caller = intent.caller if isinstance(intent, Intent) else "agent"
    target = intent.target if isinstance(intent, Intent) else intent

    # construct the destination (either service with action, or just service)
    dest = f"{target.service}:{target.action}" if target.action else target.service

    logger.info(f"~~ registered intent: {caller} -> {dest}")

    # when automatic scanning implemented, validate the intent

    # return the id to the caller
    return {"id": req_id}


@app.post("/call", dependencies=[Depends(verify_token)])
async def forward_call(call: Call) -> ProcessedReply | BunkerError:
    set_req_id(call.id)

    dest = f"{call.target.service}:{call.target.action}" if call.target.action else call.target.service
    logger.info(f"^_> forward call: {call.caller} -> {dest}")

    headers = {"x-token": api_token or ""}

    try:
        async with httpx.AsyncClient() as client:
            result = await client.post(
                f"{agent_url}/call",
                json=call.model_dump(),
                headers=headers,
                timeout=20.0
            )

        result.raise_for_status()
        agent_data = result.json()

    except httpx.TimeoutException as e:
        msg=f"request timed out"
        logger.warning(msg)
        return BunkerError(reason=msg)
    except httpx.HTTPStatusError as e:
        msg=f"unreachable: http {e.response.status_code}"
        logger.warning(msg)
        return BunkerError(reason=msg)
    except Exception as e:
        msg=f"unexpected error: {type(e).__name__}"
        logger.warning(msg)
        return BunkerError(reason=msg)

    logger.info(f"~~ agent reply received")
    logger.debug(f"~~ agent reply dump: {agent_data}")

    try:
        reply_obj = ReplyAdapter.validate_python(agent_data)
    except ValidationError as e:
        msg=f"agent data validation failed: {e}"
        logger.critical(msg)
        return BunkerError(reason=msg)

    processed = await process_reply(reply_obj)

    logger.info(f"~~ reply sent: {call.caller} -> {reply_obj.payload.get("message", "empty").lower()}")

    return processed


if __name__ == "__main__":
    import uvicorn
    logger.info("starting...")
    uvicorn.run(app, host="0.0.0.0", port=5050)
