# berserk-checker.py
# 
# subprogramm to keep track of and check the latest Berserk chapter

import os
import sys
import asyncio
import httpx
import json
from shared.transmitter import send_to_bunker
from typing import TypedDict
from pathlib import Path


SERVICE_NAME = "berserk_checker"
BASE_URL = "https://api.mangadex.org"
CURRENT_DIR = Path(__file__).resolve().parent
CACHE_FILE = CURRENT_DIR / "chapter.json"


class CacheData(TypedDict):
    chapter: int
    published: str
    times_ran: int


async def fetch():
    headers = {"User-Agent": "MangaTrackerCLI/1.0"}
    manga_id = "801513ba-a712-498c-8f57-cae55b38cc92"
    params={
        "translatedLanguage[]": "en",
        "order[chapter]": "desc",
        "limit": 1
    }

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/manga/{manga_id}/feed",
            headers=headers,
            params=params,
            timeout=10
        )
        r.raise_for_status()
        return r


async def load() -> CacheData: # loads json data
    if not CACHE_FILE.exists():
        return {}

    try: 
        with open(CACHE_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        raise ValueError("File is corrupted") from e


async def save_cache(chapter: int, time_published: str, times_ran: int) -> None: # writes into a json file
    data = {"chapter": chapter, "published": time_published, "times_ran": times_ran}
    with open(CACHE_FILE, "w") as file:
        json.dump(data, file)


async def check():
    try:
        cache = await load()
    except ValueError as e:
        await send_to_bunker(SERVICE_NAME, "error", {"message": str(e)})
        print(f"ERROR: {e}.") # here call to a log/transmitter function
        cache = {}

    times_ran = cache.get("times_ran", 0)

    try:
        request = await fetch()
    except httpx.HTTPError as e:
        raise ConnectionError(f"Couldn't access the API: {e}") from e

    data = request.json()
    chapter = data.get("data", [])[0]

    ch_num = None
    publish_date = None

    if chapter:
        attributes = chapter.get("attributes", {})

        ch_num = float(attributes.get("chapter", 0))    # attention - 0 as a default value will always make the programm think it's a new chapter.
                                                        # needed to exclude ValueError possibility. may be a better way to handle.
        publish_date = attributes.get("publishAt", "Unknown")

    last_ch = cache.get("chapter", None)


    if not last_ch:
        msg = f"First run. Keeping track of chapter {ch_num}"
    elif ch_num > last_ch:
        msg = f"Chapter {ch_num} is out!"
    else:
        msg = "No new chapter."

    payload = {"message": msg, "chapter": ch_num}

    is_agent = os.environ.get("CALLED_BY_AGENT") == "1"
    if is_agent:
        print(json.dumps({
            "service": SERVICE_NAME,
            "status": "ok",
            "payload": payload
        }))
    else:
        await send_to_bunker(SERVICE_NAME, "ok", payload)

    await save_cache(ch_num, publish_date, times_ran + 1)


if __name__ == "__main__":
    asyncio.run(check())
