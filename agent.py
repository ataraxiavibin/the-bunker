# agent.py
#
# runs services

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


class ReplyContext:
    def __init__(self, call: Call):
        self.call = call
        self.service = call.target.service
        self.action = call.target.action
        # self._start_time = time.perf_counter()
        # i may use that, but i think it's useless since i get time of the whole request path in bot
        # and only execution time is also better for diagnostics later (maybe add avg exec time in bunker db)

    def fatal(self, reason: str, stderr: str = "", returncode: int = -1, duration_ms: int = 0, payload: dict | None = None, log_details: str = None) -> ReplyError:
        log_msg = f"[FATAL] {reason} | SERVICE: {self.service}, ACTION: {self.action}, REPLY_TO: {self.call.caller}"

        if log_details:
            log_msg += f"\n--- [DEBUG DETAILS] ---\n{log_details}\n------------------"

        logger.error(log_msg)

        return ReplyError(
            service=self.service,
            action=self.action,
            reply_to=self.call.caller,
            status="fatal",
            stderr=stderr,
            returncode=returncode,
            reason=reason,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            payload=payload
        )

    def error(self, reason: str, stderr: str, returncode: int, duration_ms: int, payload: dict | None = None) -> ReplyError:
        logger.warning(f"[ERROR] {reason} | SERVICE: {self.service}, ACTION: {self.action}, REPLY_TO: {self.call.caller}")

        return ReplyError(
            service=self.service,
            action=self.action,
            reply_to=self.call.caller,
            status="error",
            stderr=stderr,
            returncode=returncode,
            reason=reason,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            payload=payload
        )

    def ok(self, stderr: str, duration_ms: int, payload: dict) -> ReplyOk:
        logger.info(f"successfull execution of {self.service}: {self.action} | REPLY_TO: {self.call.caller}")

        return ReplyOk(
            service=self.service,
            action=self.action,
            reply_to=self.call.caller,
            status="ok",
            stderr=stderr,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            payload=payload
            )


class EventContext:
    def __init__(self, target: Target):
        self.target = target
        self.service = target.service
        self.action = target.action or ""

    def fatal(self, reason: str, stderr: str = "", returncode: int = -1, duration_ms: int = 0, payload: Dict | None = None, log_details: str = None) -> EventError:
        log_msg = f"[FATAL] {reason} | SERVICE: {self.service}, ACTION: {self.action}"

        if log_details:
            log_msg += f"\n--- [DEBUG DETAILS] ---\n{log_details}\n------------------"

        logger.error(log_msg)

        return EventError(
            service=self.service,
            action=self.action,
            status="fatal",
            stderr=stderr,
            returncode=returncode,
            reason=reason,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            payload=payload
        )

    def error(self, reason: str, stderr: str, returncode: int, duration_ms: int, payload: dict | None = None) -> EventError:
        logger.warning(f"[ERROR] {reason} | SERVICE: {self.service}, ACTION: {self.action}")

        return EventError(
            service=self.service,
            action=self.action,
            status="error",
            stderr=stderr,
            returncode=returncode,
            reason=reason,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            payload=payload
        )

    def ok(self, stderr: str, duration_ms: int, payload: dict) -> EventOk:
        logger.info(f"successfull execution of {self.service}: {self.action}") # yeah, not really clear how does one see that it's event, not reply.

        return EventOk(
            service=self.service,
            action=self.action,
            status="ok",
            stderr=stderr,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            payload=payload
        )


async def execute_service(cmd: list, timeout: float = 15.0) -> ExecutionResult:
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

        logger.debug(f"successfully ran {cmd}.")
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
            reason = "permission to execute the service denied."
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

    ctx = ReplyContext(call)
    target = call.target

    logger.info(f"Received call: '{target.action}' on {target.service} for {call.caller}.")

    if target.service not in MAPPINGS:
        return ctx.fatal(f"service '{target.service}' not found.")

    if target.action not in MAPPINGS[target.service]["actions"]:
        return ctx.fatal(f"action '{target.action}' not found in '{target.service}' service.")

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

    # 1. guarantee, that stdout is there
    if not stdout:
        return ctx.fatal(reason or "service returned empty stdout", stderr=stderr, returncode=returncode, duration_ms=duration_ms)

    # 2. guarantee, that stdout is json
    try:
        parsed_stdout = json.loads(stdout)
    except json.JSONDecodeError as e:
        return ctx.fatal(f"an error occured while parsing json", stderr=stderr, returncode=returncode, duration_ms=duration_ms, log_details=stdout)

    # 3. if there's stdout, it's json.
    if returncode == 0:
        return ctx.ok(stderr=stderr, duration_ms=duration_ms, payload=parsed_stdout)
    else:
        if not reason and stderr:
            reason = stderr.strip().split('\n')[-1][:100]
        if not reason:
            reason = parsed_stdout.get("message", f"service exited with {returncode}") # in case of failure, services should print in stdout reason in "message"?

        logger.warning(f"Error from service {target.service}: {target.action} | REASON: {reason}, REPLY_to: {call.caller}")
        return ctx.error(stderr=stderr, returncode=returncode, reason=reason, duration_ms=duration_ms, payload=parsed_stdout)


async def handle_cli():
    parser = argparse.ArgumentParser(
        prog="agent",
        description="runs local services",
        exit_on_error=True
    )


    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="execute a service")

    run_parser.add_argument("service", help="service to execute (true to mappings)")
    run_parser.add_argument("action", nargs="?", help="action to complete (true to mappings)")
    run_parser.add_argument("-t", "--text", action="store_true", help="human-readable output")

    args = parser.parse_args()

    target = Target(service=args.service, action=args.action)

    ctx = EventContext(target)

    if target.service not in MAPPINGS:
        print(f"error: service '{target.service}' not found.")
        sys.exit(1)
    if target.action not in MAPPINGS[target.service]["actions"]:
        print(f"error: action '{target.action}' not found in '{target.service}.'")
        sys.exit(1)

    cmd = [sys.executable, "-m", MAPPINGS[target.service]["path"], target.action]

    result = await execute_service(cmd) # ExecutionResult

    stdout = result["stdout"]
    stderr = result["stderr"]
    returncode = result["returncode"]
    duration_ms = result["duration_ms"]
    reason = result["reason"]

    parsed_stdout = None

    if not stdout:
        fail_reason = reason or "service returned no stdout"
        print(f"{fail_reason} | stderr: {stderr}, exit code: {returncode}")
        ctx.fatal(reason=fail_reason, stderr=stderr, returncode=returncode, duration_ms=duration_ms)
        sys.exit(1) # service exit code doesn't matter, since service doesn't follow the systems contract

    try:
        parsed_stdout = json.loads(stdout)
    except json.JSONDecodeError as e:
        print(f"json parse error: {e}, stdout: {stdout}")
        ctx.fatal(f"an error occured while parsing json", stderr=stderr, returncode=returncode, duration_ms=duration_ms, log_details=stdout)
        sys.exit(1)

    # from now we're sure that parsed_stdout exists and it's valid json

    if args.text:
        msg = parsed_stdout["message"]
    else:
        msg = parsed_stdout

    if returncode == 0:
        print(msg)
        return ctx.ok(stderr=stderr, duration_ms=duration_ms, payload=parsed_stdout)
    else:
        if not reason and stderr:
            reason = stderr.strip().split('\n')[-1][:100]
        if not reason:
            reason = parsed_stdout.get("message", f"service exited with {returncode}") # in case of failure, services should print in stdout reason in "message"?

        print(msg)
        ctx.error(reason=reason, stderr=stderr, returncode=returncode, duration_ms=duration_ms, payload=parsed_stdout)
        sys.exit(returncode)


@app.get("/ping")
async def handle_ping():
    logger.debug("Got ping")
    return {"status": "alive"}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        asyncio.run(handle_cli())
    else: # this is not used since i launch through uvicorn command, but it bugs me if i don't add it
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=5051)
