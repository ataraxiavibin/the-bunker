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
from fastapi import FastAPI, Header, HTTPException, Request, Depends
from typing import Dict, Any, TypedDict, Optional
from dotenv import load_dotenv
from loguru import logger

from shared.models import Call, Target, Reply, ReplyOk, ReplyError, Event, EventOk, EventError, Intent
from shared.transmitter import send_to_bunker, get_id
from shared.auth import verify_token
from shared.logger import setup_logger, set_req_id

logger = setup_logger("agent", "./logs/agent.log")

app = FastAPI()

load_dotenv()
api_token = os.environ.get("API_TOKEN")

NAME="agent"

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

    def fatal(self, id: str, reason: str, stderr: str = "", returncode: int = -1, duration_ms: int = 0, payload: dict | None = None, log_details: str = None) -> ReplyError:
        logger.critical(f"fatal error: {reason.lower()}")

        if log_details:
            logger.debug(f"fatal dump: {log_details}")

        return ReplyError(
            id=id,
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

    def error(self, id: str, reason: str, stderr: str, returncode: int, duration_ms: int, payload: dict | None = None) -> ReplyError:
        logger.error(f"execution failed: {reason.lower()}")

        return ReplyError(
            id=id,
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

    def ok(self, id: str, stderr: str, duration_ms: int, payload: dict) -> ReplyOk:
        logger.info(f"~~ execution ok ({duration_ms} ms)")

        return ReplyOk(
            id=id,
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

    def fatal(self, id: str, reason: str, stderr: str = "", returncode: int = -1, duration_ms: int = 0, payload: Dict | None = None, log_details: str = None) -> EventError:
        logger.critical(f"event fatal: {reason.lower()}")

        if log_details:
            logger.debug(f"event dump: {log_details}")

        logger.error(log_msg)

        return EventError(
            id=id,
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

    def error(self, id: str, reason: str, stderr: str, returncode: int, duration_ms: int, payload: dict | None = None) -> EventError:
        logger.error(f"event failed: {reason.lower()}")

        return EventError(
            id=id,
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

    def ok(self, id: str, stderr: str, duration_ms: int, payload: dict) -> EventOk:
        logger.info(f"~~ event ok ({duration_ms} ms)")

        return EventOk(
            id=id,
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
    cmd_str = " ".join(cmd)

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

        logger.debug(f"process finished {cmd_str}.")
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

        logger.error(f"process timed out ({timeout}s): {cmd_str}")

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

        logger.error(f"os execution failure: {type(e).__name__.lower()} | {cmd_str}") # maybe get rid of that pipe cuz it doesn't follow the stylistics
        logger.debug(f"os-error dump: {e}")

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



@app.post("/call", dependencies=[Depends(verify_token)])
async def run_call(call: Call, request: Request, x_token: str = Header(...)) -> Reply:
    ctx = ReplyContext(call)
    target = call.target
    req_id = call.id

    set_req_id(req_id)

    logger.info(f"^_> received call: {call.caller} -> {target.service}:{target.action}")

    if target.service not in MAPPINGS:
        return ctx.fatal(id=req_id, reason=f"service '{target.service}' not found.")

    if target.action not in MAPPINGS[target.service]["actions"]:
        return ctx.fatal(id=req_id, reason=f"action '{target.action}' not found in '{target.service}' service.")

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
        return ctx.fatal(id=req_id, reason=reason or "service returned empty stdout", stderr=stderr, returncode=returncode, duration_ms=duration_ms)

    # 2. guarantee, that stdout is json
    try:
        parsed_stdout = json.loads(stdout)
    except json.JSONDecodeError as e:
        return ctx.fatal(id=req_id, reason=f"an error occured while parsing json", stderr=stderr, returncode=returncode, duration_ms=duration_ms, log_details=stdout)

    # 3. if there's stdout, it's json.
    if returncode == 0:
        return ctx.ok(id=req_id, stderr=stderr, duration_ms=duration_ms, payload=parsed_stdout)
    else:
        if not reason and stderr:
            reason = stderr.strip().split('\n')[-1][:100]
        if not reason:
            reason = parsed_stdout.get("message", f"service exited with {returncode}") # in case of failure, services should print in stdout reason in "message"?

        return ctx.error(id=req_id, stderr=stderr, returncode=returncode, reason=reason, duration_ms=duration_ms, payload=parsed_stdout)


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
    intent = Intent(caller=NAME, target=target)

    register_res = await get_id(intent)

    if not register_res:
        print("couldn't resolve id for the request")
        sys.exit(1)

    req_id = register_res.json()["id"]

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
        ctx.fatal(id=req_id, reason=fail_reason, stderr=stderr, returncode=returncode, duration_ms=duration_ms)
        sys.exit(1) # service exit code doesn't matter, since service doesn't follow the systems contract

    try:
        parsed_stdout = json.loads(stdout)
    except json.JSONDecodeError as e:
        print(f"json parse error: {e}, stdout: {stdout}")
        ctx.fatal(id=req_id, reason=f"an error occured while parsing json", stderr=stderr, returncode=returncode, duration_ms=duration_ms, log_details=stdout)
        sys.exit(1)

    # from now we're sure that parsed_stdout exists and it's valid json

    if args.text:
        msg = parsed_stdout["message"]
    else:
        msg = parsed_stdout


    print(msg)
    if returncode == 0:
        event = ctx.ok(id=req_id, stderr=stderr, duration_ms=duration_ms, payload=parsed_stdout)
    else:
        if not reason and stderr:
            reason = stderr.strip().split('\n')[-1][:100]
        if not reason:
            reason = parsed_stdout.get("message", f"service exited with {returncode}") # in case of failure, services should print in stdout reason in "message"?
        event = ctx.error(id=req_id, reason=reason, stderr=stderr, returncode=returncode, duration_ms=duration_ms, payload=parsed_stdout)

    if not await send_to_bunker(event):
        logger.error(f"failed to send event to bunker") # maybe add queuing, so I don't lose info in logs. for future at least
    sys.exit(returncode or 0)


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
