# connect.py
#
# connects to airpods

import subprocess
import argparse
from shared.transmitter import send_to_bunker

SERVICE_NAME = "pods_connect"
MAC = "34:0E:22:C3:31:79"

def run_bt_command(*args) -> str:
    result = subprocess.run(
        ['bluetoothctl', *args], 
        capture_output=True,
        text=True
    )
    return result.stdout


def log_and_send(status: str, msg: str) -> bool:
    print(f"LOG: {msg}")
    send_to_bunker(SERVICE_NAME, status, {"message": msg})
    
    return True # TODO: check if connection is valid and the bunker is online
    # TODO: maybe add log_and_send to a shared file, since it's gonna be widely used


def connect_headphones() -> bool:
    return "Connection successful" in run_bt_command('connect', MAC)


def disconnect_headphones() -> bool:
    return "Disconnection successful" in run_bt_command('disconnect', MAC)


def check_connection() -> bool:
    return MAC in run_bt_command('devices', 'Connected')

def main():
    if check_connection():
        log_and_send("ok", "Already connected. Initiating disconnection.")

        if disconnect_headphones():
            log_and_send("ok", "Successfully disconnected.")
        else:
            log_and_send("warning", "Failed to disconnect.") 
    else:
        if connect_headphones():
            log_and_send("ok", "Connection successful.")
        else:
            log_and_send("warning", "Failed to connect.")
  

if __name__ == "__main__":
    main()
