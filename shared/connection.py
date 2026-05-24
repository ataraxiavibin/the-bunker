# connection.py 
#
# checks, if bunker exists..

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BUNKER_URL = os.environ.get("BUNKER_URL")

def is_bunker_alive(timeout: int = 2) -> bool:
    try:
        response = requests.get(BUNKER_URL+"/ping", timeout=timeout)

        if response.status_code == 200:
            return True
        
        return False

    except requests.exceptions.RequestException:
        return False

def main():
    print(f"Pinging Bunker at {BUNKER_URL}...")

    if is_bunker_alive():
        print("Bunker is ONLINE and accessible.")
    else:
        print("Bunker is OFFLINE or unreachable.")


if __name__ == "__main__":
    main()
