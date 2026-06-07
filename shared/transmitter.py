# transmitter.py

import requests
import httpx
import os
from typing import Dict, Any
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
        logger.warning(f"Couldn't reach Bunker: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error: {e}")
        return False

    return True

def call_to_bunker(service: str, target: Dict[str, str]):
    headers = {"x-token": API_TOKEN}
    data = {
        "service": service,
        "target": target
    }

    try:
        response = requests.post(BUNKER_URL+"/call", json=data, headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to send call to bunker: {e}")
        return False

    return True

