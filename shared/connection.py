# connection.py 
#
# checks, if bunker exists..

import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

BUNKER_URL = os.environ.get("BUNKER_URL")

async def is_bunker_alive(timeout: int = 2) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(BUNKER_URL+"/ping", timeout=timeout)

            if response.status_code == 200:
                return True
        
            return False

    except httpx.HTTPError:
        return False

async def main():
    print(f"Pinging Bunker at {BUNKER_URL}...")

    if await is_bunker_alive():
        print("Bunker is ONLINE and accessible.")
    else:
        print("Bunker is OFFLINE or unreachable.")


if __name__ == "__main__":
    asyncio.run(main())
