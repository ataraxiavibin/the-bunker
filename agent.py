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
import asyncio
import json
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv
from loguru import logger

from bunker import Call, Target, Reply

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
        "actions": ["connect", "disconnect", "reconnect"] 
    }
}

@app.post("/call")
async def run_call(call: Call, request: Request, x_token: str = Header(...)) -> Reply:
    if x_token != api_token:
        raise HTTPException(status_code=403, detail="Forbidden")

    target = call.target

    if target.service not in MAPPINGS:
        return Reply(
                service=target.service,
                reply_to=call.caller,
                status="fatal",
                payload={
                    "reason": "File not found."
                }
            ) 

    if target.action not in MAPPINGS[target.service]["actions"]:
        return Reply(
            service=target.service,
            reply_to=call.caller,
            status="fatal",
            payload={
                "reason": f"Action {target.action} not found in {target.service} service."
            }
        )

    cmd = [sys.executable, "-m", MAPPINGS[target.service]["path"], target.action, "--json"]

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=15.0
        )
        stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        parsed_stdout = stdout
        try:
            parsed_stdout = json.loads(stdout)
        except json.JSONDecodeError as e:
            pass # TODO: probably send status fatal

        returncode = proc.returncode
    except asyncio.TimeoutError as e:
        if proc:
            try:
                proc.kill()
                await proc.wait()
            except ProcessLookupError:
                pass
        return Reply(
            service=target.service,
            reply_to=call.caller,
            status="fatal",
            payload={
                "reason": "Process execution timed out"
            }
        )
    except Exception as e:
        if proc and proc.returncode is None:
            try:
                proc.kill()
                await proc.wait()
            except ProcessLookupError:
                pass
        return Reply(
            service=target.service,
            reply_to=call.caller,
            status="fatal",
            payload={
                "reason": f"Execution error: {e}"
            }
        )

    status = "ok" if returncode == 0 else "error"
    return Reply(
        service=target.service,
        reply_to=call.caller,
        status=status,
        payload={
            "stdout": parsed_stdout,
            "stderr": stderr,
            "returncode": returncode
        }
    )
        # TODO: normalize JSON returns and make a standardized stdout system in services/agent.


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5051)
