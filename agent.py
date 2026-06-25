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
        reason = f"service '{target.service}' not found."
        logger.warning(f"[FATAL] {reason} | ACTION: {target.action}, REPLY_TO: {call.caller}")
        return ReplyError(
                service=target.service,
                action=target.action,
                reply_to=call.caller,

                status="fatal",
                stderr="",
                returncode=-1,
                reason=reason,

                timestamp=datetime.now(timezone.utc),
                duration_ms=0,

                payload=None
        )

    if target.action not in MAPPINGS[target.service]["actions"]:
        reason = f"action '{target.action}' not found in '{target.service}' service."
        logger.warning(f"[FATAL] {reason} | REPLY_TO: {call.caller}")
        return ReplyError(
                service=target.service,
                action=target.action,
                reply_to=call.caller,

                status="fatal",
                stderr="",
                returncode=-1,
                reason=reason,

                timestamp=datetime.now(timezone.utc),
                duration_ms=0,

                payload=None
        )

    logger.info(f"Executing '{target.action}' on {target.service} for {call.caller}.")

    # use subprocess to make the system language-agnostic.
    cmd = [sys.executable, "-m", MAPPINGS[target.service]["path"], target.action]

    result = await execute_service(cmd)

    stdout = result["stdout"]
    stderr = result["stderr"]
    returncode = result["returncode"]
    duration_ms = result["duration_ms"]
    reason = result["reason"]

    parsed_stdout = None

    if stdout:
        try:
            parsed_stdout = json.loads(stdout)
        except json.JSONDecodeError as e:
            logger.critical(f"[FATAL] An error occured while parsing JSON | (unparsed) STDOUT: {stdout}")
            return ReplyError(
                service=target.service,
                action=target.action,
                reply_to=call.caller,

                status="fatal",
                stderr=stderr,
                returncode=returncode,
                reason=f"failed to parse service stdout; more at logs/agent.log",
                timestamp=datetime.now(timezone.utc),

                duration_ms=duration_ms,
                payload=None
            )

    if returncode == 0:
        logger.info(f"Successfull execution of {target.service}: {target.action} | REPLY_TO: {call.caller}")
        return ReplyOk(
            # metadata
            service=target.service,
            action=target.action,
            reply_to=call.caller,
            # diagnostic
            status="ok",
            stderr=stderr,
            timestamp=datetime.now(timezone.utc),
            # used data
            duration_ms=duration_ms,
            payload=parsed_stdout
        )
    else:
        if not reason and stderr:
            reason = stderr.strip().split('\n')[-1][:100]
        if not reason:
            reason = parsed_stdout.get("message", f"service exited with {returncode}")

        logger.warning(f"[FATAL]: Error from service {target.service}: {target.action} | REASON: {reason}, REPLY_to: {call.caller}")
        return ReplyError(
                service=target.service,
                action=target.action,
                reply_to=call.caller,

                status="fatal",
                stderr=stderr,
                returncode=returncode,
                reason=reason,

                timestamp=datetime.now(timezone.utc),
                duration_ms=duration_ms,
                payload=parsed_stdout
        )

async def handle_cli():
    parser = argparse.ArgumentParser(
        prog="agent",
        description="runs local services",
        exit_on_error=False
    )


    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="execute a service")

    run_parser.add_argument("file", help="file to execute (true to mappings)")
    run_parser.add_argument("action", nargs="?", help="action to complete (true to mappings)")
    run_parser.add_argument("-t", "--text", action="store_true", help="human-readable output")

    args = parser.parse_args()
    if args.command:
        target = Target(service=args.file, action=args.action)

    # so, TODO:


@app.get("/ping")
async def handle_ping():
    logger.debug("Got ping")
    return {"status": "alive"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5051)
    # asyncio.run(handle_cli())
