# agent.py
#
# runs services
# 
# just a test idea:
# it will be a separate server from bunker, which purpose will solely be:
# run local services and get the results back to bunker.
# this way, every device can have their own local services and Bunker system can work with many different devices at the same time while not taking up many resources.

import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv
from loguru import logger

app = FastAPI()

load_dotenv()
api_token = os.environ.get("API_TOKEN")

logger.add("./logs/agent.log", rotation="10 MB", retention="30 days", level="INFO")

# name: path, actions
MAPPINGS = {
    "berserk_checker": {
        "path": "./services/berserk_checker/checker.py", 
        "actions": ["check"]
    },
    "pods_connect": {
        "path": "./services/pods_connect/connect.py", 
        "actions": ["connect", "disconnect", "reload"]
    }
}

# two paths:
# - subprocess: the programming language will no longer matter (probably the best option)
# - import: just python, but kinda easier on eyes idk.

@app.post("/call")
async def run_call():
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5051)
