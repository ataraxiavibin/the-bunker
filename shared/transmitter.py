# transmitter.py

import httpx
import os
from typing import Dict, Any
from bunker import Call
from dotenv import load_dotenv
from loguru import logger

logger.add("./logs/transmitter.log", rotation="2 MB", retention="7 days", level="INFO")

load_dotenv()

BUNKER_URL = os.environ.get("BUNKER_URL")
API_TOKEN = os.environ.get("API_TOKEN") 

async def send_to_bunker(service: str, status: str, payload: Dict[str, Any]):
    headers = {"x-token": API_TOKEN}
    data = {
        "service": service,
        "status": status,
        "payload": payload
    }
    try:
        async with httpx.AsyncClient() as client: 
            r = await client.post(
                BUNKER_URL+"/event",
                json=data,
                headers=headers,
                timeout=5
            )
    except httpx.HTTPError as e:
        logger.error(f"Couldn't reach Bunker: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

    return True

async def call_to_bunker(caller: str, target: Dict[str, str]): # TODO: just use Call; maybe add it to shared/models
    headers = {"x-token": API_TOKEN}
    data = {
        "caller": caller,
        "target": target
    }
    logger.info(f"Calling from {data["caller"]} -> {data["target"]["service"]} to {data["target"]["action"]}")

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
        logger.warning(f"Couldn't reach Bunker: {e}")
        return False
    except Exception as e:
        logger.warning(f"Failed to send call to bunker: {e}")
        return False

    logger.info(f"Returned: {r}")
    return r

