# transmitter.py

import requests
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

BUNKER_URL = os.environ.get("BUNKER_URL")
API_TOKEN = os.environ.get("API_TOKEN") 

def send_to_bunker(source: str, status: str, payload: Dict[str, Any]):
    headers = {"x-token": API_TOKEN}
    data = {
        "source": source,
        "status": status,
        "payload": payload
    }
    try:
        response = requests.post(BUNKER_URL+"/event", json=data, headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send event to bunker: {e}")

def call_to_bunker(source: str, target: Dict[str, str]):
    headers = {"x-token": API_TOKEN}
    data = {
        "source": source,
        "target": target
    }

        response = requests.post(BUNKER_URL+"/event", json=data, headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send event to bunker: {e}")
