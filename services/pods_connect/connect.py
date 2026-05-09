# connect.py
#
# connects to airpods

import subprocess
from shared.transmitter import send_to_bunker

SOURCE = "pods_connect"
MAC = "34:0E:22:C3:31:79"

def connect_headphones() -> bool:
    result = subprocess.run(['bluetoothctl', 'connect', MAC], capture_output=True, text=True)
    if "Connection successful" in result.stdout:
        return True

    return False


def check_connection() -> bool:
    result = subprocess.run(['bluetoothctl', 'devices', 'Connected'], capture_output=True, text=True)
    if MAC in result.stdout:
        return True


def main():
    if check_connection():
        msg = "Already connected."
        print(f"LOG: {msg}")
        send_to_bunker(SOURCE, "ok", {"message": msg})

        return

    if connect_headphones():
        msg = "Connection successful."
        print(f"LOG: {msg}")
        send_to_bunker(SOURCE, "ok", {"message": msg})
    else:
        msg = "Failed to connect."
        print(f"LOG: {msg}")
        send_to_bunker(SOURCE, "warning", {"message": msg})


if __name__ == "__main__":
    main()
