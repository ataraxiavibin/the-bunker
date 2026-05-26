# agent.py
#
# runs services
# 
# just a test idea:
# it will be a separate server from bunker, which purpose will solely be:
# run local services and get the results back to bunker.
# this way, every device can have their own local services and Bunker system can work with many different devices at the same time while not taking up many resources.

import os
import sys
import subprocess
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv
from loguru import logger

from bunker import Call, Target

app = FastAPI()

load_dotenv()
api_token = os.environ.get("API_TOKEN")

logger.add("./logs/agent.log", rotation="10 MB", retention="30 days", level="INFO")

# name: path, actions
MAPPINGS = {
    "berserk_checker": {
        "path": "services.berserk_checker.checker", 
        "actions": ["check"]
    },
    "pods_connect": {
        "path": "services.pods_connect.connect", 
        "actions": ["connect", "disconnect", "reload"]
    }
}

@app.post("/call")
async def run_call(call: Call, request: Request, x_token: str = Header(...)):
    if x_token != api_token:
        raise HTTPException(status_code=403, detail="Forbidden")

    source_call = call.source
    target = call.target

    if target.service in MAPPINGS:
        if target.action in MAPPINGS[target.service]["actions"]:
            cmd = [sys.executable, "-m", MAPPINGS[target.service]["path"], target.action]
            result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )

            return {"source": target.action+" via agent","status": "ok", "payload": result.stdout }
    else:
        return {"source": call.source, "status": "error"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5051)
