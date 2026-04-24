# transmitter.py

import requests
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

BUNKER_URL = "http://localhost:5050/event"
API_TOKEN = os.environ.get("API_TOKEN") 

def send_to_bunker(source: str, status: str, payload: Dict[str, Any]):
    headers = {"x-token": API_TOKEN}
    data = {
        "source": source,
        "status": status,
        "payload": payload
    }
    try:
        response = requests.post(BUNKER_URL, json=data, headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send event to bunker: {e}")
