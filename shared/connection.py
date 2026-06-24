# connection.py 
#
# checks, if bunker exists..

import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

BUNKER_URL = os.environ.get("BUNKER_URL")
AGENT_URL = os.environ.get("AGENT_URL")

async def _check_url(client: httpx.AsyncClient, url: str, timeout: int) -> bool:
    try:
        response = await client.get(url, timeout=timeout)
        return response.status_code == 200 # True/False
    except httpx.RequestError:
        return False

async def is_system_up(timeout: int = 3) -> dict[str, bool]:
    # easily extendable
    endpoints = {
        "bunker": f"{BUNKER_URL}/ping",
        "agent": f"{AGENT_URL}/ping" # in future, agents will have their own names, for example: agent-aixarata
    }

    async with httpx.AsyncClient() as client:
        tasks = {
            name: _check_url(client, url, timeout)
            for name, url in endpoints.items()
        }

        results = await asyncio.gather(*tasks.values())

        # {"bunker": True, "agent": False}
        return dict(zip(tasks.keys(), results))

async def check_connection():
    status = await is_system_up()
    print(status)
    for key, is_up in status.items():
        msg = "is running." if is_up else "is offline."
        print(f"{key} {msg}")
    


if __name__ == "__main__":
    asyncio.run(check_connection())
