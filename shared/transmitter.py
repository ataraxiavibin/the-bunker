# transmitter.py

import httpx
import os
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel
from shared.models import Call, Event, Intent
from dotenv import load_dotenv
from loguru import logger as base_logger

logger = base_logger.bind(module="transm")

from shared.logger import set_req_id

load_dotenv()

BUNKER_URL = os.environ["BUNKER_URL"]
API_TOKEN = os.environ["API_TOKEN"]

async def send_to_bunker(event: Event):
    set_req_id(event.id)
    headers = {"x-token": API_TOKEN}
    data = event.model_dump(mode="json")
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                BUNKER_URL+"/event",
                json=data,
                headers=headers,
                timeout=5
            )
            r.raise_for_status()
    except httpx.HTTPError as e:
        logger.error(f"network failure: {e}")
        return False
    except Exception as e:
        logger.error(f"unexpected error: {e}")
        return False

    return True

async def call_to_bunker(call: Call):
    set_req_id(call.id)
    headers = {"x-token": API_TOKEN}
    data = call.model_dump()

    dest = f"{call.target.service}:{call.target.action}" if call.target.action else call.target.service

    logger.info(f"transmitting call: {call.caller} -> {dest}")

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                BUNKER_URL+"/call",
                json=data,
                headers=headers,
                timeout=25
            )
            r.raise_for_status()
    except httpx.HTTPError as e:
        logger.error(f"network failure: {e}")
        return False
    except Exception as e:
        logger.error(f"unexpected error: {e}")
        return False

    logger.info(f"bunker response received ({r.status_code})")
    return r

async def get_id(intent: Intent):
    headers = {"x-token": API_TOKEN}

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                BUNKER_URL+"/register",
                json=intent.model_dump(),
                headers=headers,
                timeout=5,
            )
            r.raise_for_status()
    except httpx.HTTPError as e:
        logger.error(f"network failure: {e}")
        return False
    except Exception as e:
        logger.error(f"unexpected error: {e}")
        return False

    # do not log that lol
    return r

