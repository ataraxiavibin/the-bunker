# connect.py
#
# connects to airpods

import os
import sys
import json
import asyncio
import subprocess
from shared.transmitter import send_to_bunker
from shared.parser import get_args

SERVICE_NAME = "pods_connect"
MAC = "34:0E:22:C3:31:79"
BT_TIMEOUT = 10

async def bt(*args) -> str:
    try:
        proc = await asyncio.create_subprocess_exec(
            'bluetoothctl', *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout_bytes, _ = await asyncio.wait_for(
            proc.communicate(),
            timeout=BT_TIMEOUT
        )

        return stdout_bytes.decode("utf-8", errors="replace")

    except asyncio.TimeoutError:
        if proc:
            try:
                proc.kill()
                await proc.wait()
            except ProcessLookupError:
                pass
            return "Process timed out." # return a string so no TypeError
    except Exception as e:
        return f"Unexpected error: {e}" # same here


# async def log_and_send(status: str, msg: str, print_json: bool) -> None:
#     if print_json:
#         print(json.dumps({
#             "status": status,
#             "payload": {
#                 "message": msg
#             }
#         }))
#     else:
#         print(f"LOG: {msg}")
#         await send_to_bunker(SERVICE_NAME, status, {"message": msg})


#TODO: refactor all of this to return the reason from bluetoothctl. honestly, almost everything here must be rewritten.
async def connect() -> bool: return "Connection successful" in await bt("connect", MAC)
async def disconnect() -> bool: return "Disconnection successful" in await bt("disconnect", MAC)
async def reconnect() -> bool: await bt("disconnect", MAC); return await connect()
async def check_connection() -> bool: return MAC in await bt("devices", "Connected")

ACTIONS = {
    "connect": (connect, "Connected.", "Failed to connect."),
    "disconnect": (disconnect, "Disconnected.", "Failed to disconnect."),
    "reconnect": (reconnect, "Reconnect.", "Failed to reconnect.")
}

async def main():
    args = get_args(SERVICE_NAME, "bunker microservice to control bluetooth connection", list(ACTIONS))

    action = args.action or ("disconnect" if await check_connection() else "connect")

    print_json = args.json

    fn, ok_msg, err_msg = ACTIONS[action]
    success = await fn()

    # await log_and_send("ok" if success else "error", ok_msg if success else err_msg, print_json)

    if not success:
        print(err_msg, file=sys.stderr) # since the code is written horribly, we don't have anything to send to stderr that contains any remote reason
        sys.exit(1)

    print(json.dumps({"message": ok_msg}))
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
