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
BT_TIMEOUT = 8

def bt(*args) -> str:
    return subprocess.run(
        ['bluetoothctl', *args], 
        capture_output=True,
        text=True,
        timeout=BT_TIMEOUT
    ).stdout


async def log_and_send(status: str, msg: str) -> None:
    is_agent = os.environ.get("CALLED_BY_AGENT") == "1"
    if is_agent:
        print(json.dumps({
            "service": SERVICE_NAME,
            "status": status,
            "message": msg 
        }))
    else:
        print(f"LOG: {msg}")
        await send_to_bunker(SERVICE_NAME, status, {"message": msg})
    
    # TODO: mb check if connection is valid and the bunker is online
    # TODO: maybe add log_and_send to a shared file, since it's gonna be widely used


def connect() -> bool: return "Connection successful" in bt("connect", MAC)
def disconnect() -> bool: return "Disconnection successful" in bt("disconnect", MAC)
def reconnect() -> bool: bt("disconnect", MAC); return connect()
def check_connection() -> bool: return MAC in bt("devices", "Connected") 

ACTIONS = {
    "connect": (connect, "Connected.", "Failed to connect."),
    "disconnect": (disconnect, "Disconnected.", "Failed to disconnect."),
    "reconnect": (reconnect, "Reconnect.", "Failed to reconnect.")
} # tbh i hate how it logs no reason, but it works. 

async def main():
    args = get_args(SERVICE_NAME, "bunker microservice to control bluetooth connection", list(ACTIONS))
    
    action = args.action or ("disconnect" if check_connection() else "connect")
    # to be honest, this is a lot of "not explicit" architectural behaviour, this sucks.

    fn, ok_msg, err_msg = ACTIONS[action]
    success = fn()

    await log_and_send("ok" if success else "error", ok_msg if success else err_msg)
  

if __name__ == "__main__":
    asyncio.run(main())
