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
import asyncio
import json
import argparse
import time
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, TypedDict, Optional
from dotenv import load_dotenv
from loguru import logger

from shared.models import Call, Target, Reply, ReplyOk, ReplyError, Event, EventOk, EventError

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

class ExecutionResult(TypedDict):
    stdout: str
    stderr: str
    returncode: int
    duration_ms: int
    reason: Optional[str]


async def execute_service(cmd: list, timeout: float = 15.0) -> ExecutionResult:
    # it's a stdout/stderr we are looking for.
    # transforming it into event/reply is gonna be original caller-functions duty.
    start_time = time.perf_counter()
    proc = None

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout
        )

        stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
        returncode = proc.returncode
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        logger.debug(f"Successfully ran {cmd}.")
        return ExecutionResult(
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            duration_ms=duration_ms,
            reason=None # all went smoothly on the execution part
        )
    except asyncio.TimeoutError as e:
        if proc:
            try:
                proc.kill()
                await proc.wait()
            except ProcessLookupError:
                pass

        logger.error(f"Service timed out | CMD: {cmd}\n{e}")

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return ExecutionResult(
            stdout="",
            stderr="",
            returncode=-1,
            duration_ms=duration_ms,
            reason=f"service timed out after {timeout} seconds."
        )
    except Exception as e:
        if proc and proc.returncode is None:
            try:
                proc.kill()
                await proc.wait()
            except ProcessLookupError:
                pass

        logger.error(f"OS-level execution failure for {cmd}: {type(e).__name__}: {e}")

        if isinstance(e, FileNotFoundError):
            reason = "executable file not found."
        elif isinstance(e, PermissionError):
            reason = "permission denied to execute the service."
        else:
            reason = f"failed to launch the service process: {type(e).__name__}"

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return ExecutionResult(
            stdout="",
            stderr="",
            returncode=-2,
            duration_ms=duration_ms,
            reason=reason
        )



@app.post("/call")
async def run_call(call: Call, request: Request, x_token: str = Header(...)) -> Reply:
    if x_token != api_token:
        logger.warning(f"Failed auth attempt from '{request.client.host}'")
        raise HTTPException(status_code=403, detail="Forbidden")

    target = call.target
    logger.info(f"Received call: '{target.action}' on {target.service} for {call.caller}.")

    if target.service not in MAPPINGS:
        logger.warning(f"Service '{target.service}' not found. | ACTION: {target.action}, REPLY_TO: {call.caller}")
        return Reply(
                service=target.service,
                reply_to=call.caller,
                status="fatal",
                payload={
                    "reason": "File not found."
                }
            ) 

    if target.action not in MAPPINGS[target.service]["actions"]:
        logger.warning(f"Action '{target.action}' not found in '{target.service}'. | REPLY_TO: {call.caller}")
        return Reply(
            service=target.service,
            reply_to=call.caller,
            status="fatal",
            payload={
                "reason": f"Action '{target.action}' not found in '{target.service}' service"
            }
        )

    logger.info(f"Executing '{target.action}' on {target.service} for {call.caller}.")

    # use subprocess to make the system language-agnostic.
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
            logger.error(f"An error occured while parsing JSON | (unparsed) STDOUT: {stdout}")
            return Reply(
                service=target.service,
                reply_to=call.caller,
                status="fatal",
                payload={
                    "reason": f"An error occured while parsing JSON: {e}"
                }
            )

        returncode = proc.returncode
    except asyncio.TimeoutError as e:
        if proc:
            try:
                proc.kill()
                await proc.wait()
            except ProcessLookupError:
                pass
        logger.error(f"Process of '{target.service}' timed out | ACTION: {target.action}")
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
        logger.error(f"Execution error of '{target.service}' | {e}")
        return Reply(
            service=target.service,
            reply_to=call.caller,
            status="fatal",
            payload={
                "reason": f"Execution error: {e}"
            }
        )

    status = "ok" if returncode == 0 else "error"
    logger.info(f"Reply sent to '{call.caller}'. For more details, look at logs/bunker.log | SERVICE: {target.service}, ACTION: {target.action}, STATUS: {status}")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5051)
