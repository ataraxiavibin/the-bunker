# bot.py
#
# a Telegram bot that I can touch, to use with the bunker system
# cool but useless idea! i'm in.

import os
import time
import asyncio
import json
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError

from shared.connection import is_system_up
from shared.transmitter import call_to_bunker, get_id
from shared.models import Call, Intent, Target, ProcessedReplyError, ProcessedReplyOk, BunkerError
from bot.tui import BunkerTUI

from loguru import logger
from shared.logger import setup_logger, set_req_id

logger = setup_logger("bot", log_file=None) # maybe there will be a log file for the bot, dunno

NAME = "bot"

load_dotenv()
tokenbot = os.environ["BOT_API"]

bot = Bot(token=tokenbot, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp= Dispatcher()

async def execute_bunker_call(target: Target) -> tuple[dict | None, str | None]:
    """
    makes intent model, gets id from bunker, calls bunker
    """

    intent = Intent(caller=NAME, target=target)
    register_res = await get_id(intent)

    if not register_res:
        return None, "bunker did not register the request"

    try:
        req_id = register_res.json()["id"]
    except (ValueError, KeyError, TypeError):
        return None, "failed to parse intent registration id"

    set_req_id(req_id)

    call = Call(id=req_id, caller=NAME, target=target)
    response = await call_to_bunker(call)

    if not response or getattr(response, "status_code", None) != 200:
        return None, "no response, cannot confirm."

    try:
        data = response.json()
    except ValueError:
        return None, "failed to parse bunker response payload"

    status = data.get("status", "fatal")

    if status in ["error", "fatal"]:
        reason = data.get("reason", "unknown internal error")
        return None, reason

    payload = data.get("payload")
    return payload, None


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply(BunkerTUI.welcome())

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    msg = BunkerTUI.box(
        title="help manual",
        lines=[
            "/bunker    :: get system status",
            "/pods      :: control pods connectivity",
            "   +-- args: [connect, disconnect, reconnect]",
            "/chapter   :: check berserk chapter release"
        ]
    )

    await message.answer(msg)


@dp.message(Command("chapter"))
async def cmd_chapter(message: types.Message):
    sent_msg = await message.reply(BunkerTUI.action("executing..."))
    start_time = time.perf_counter()

    action = "check"
    target = Target(service="berserk_checker", action=action)

    payload, err_reason = await execute_bunker_call(target)


    latency = int((time.perf_counter() - start_time) * 1000)

    if err_reason:
        diag_nodes = None
        if any(keyword in err_reason.lower() for keyword in ["unreachable", "connecterror", "no response", "timed out", "timeout", "did not register", "internal error"]):
            diag_nodes = await is_system_up()

        await sent_msg.edit_text(BunkerTUI.error(err_reason, diag_nodes, latency))
        return

    chapter = payload.get("chapter", "unknown")
    msg_text = payload.get("message", "ok")

    final_text = f"{msg_text}\n~~ current chapter: {chapter}"
    await sent_msg.edit_text(BunkerTUI.success(final_text, latency=latency))


@dp.message(Command("pods"))
async def cmd_pods(message: types.Message, command: CommandObject):
    action = command.args

    valid_actions = ["connect", "disconnect", "reconnect"]

    if not action or action not in valid_actions:
        return await message.reply(BunkerTUI.fatal("unknown arg. read /help."))

    sent_msg = await message.reply(BunkerTUI.action("executing..."))

    start_time = time.perf_counter()

    target = Target(service="pods_connect", action=action)
    payload, err_reason = await execute_bunker_call(target)

    latency = int((time.perf_counter() - start_time) * 1000)
    if err_reason:
        diag_nodes = None
        if any(keyword in err_reason.lower() for keyword in ["unreachable", "connecterror", "no response", "timed out", "timeout", "did not register", "internal error"]):
            diag_nodes = await is_system_up()

        await sent_msg.edit_text(BunkerTUI.error(err_reason, diag_nodes, latency))
        return

    msg_text = payload["message"]
    await sent_msg.edit_text(BunkerTUI.success(msg_text, latency))


@dp.message(Command("bunker", "status", "c"))
@dp.message(F.text.lower() == "check bunker connection")
async def check_connection(message: types.Message):
    start_time = time.perf_counter()
    result = await is_system_up()
    latency = int((time.perf_counter() - start_time) * 1000)

    msg = BunkerTUI.status_grid(result, latency)
    await message.reply(msg)


@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    await message.reply(BunkerTUI.clean_screen())

async def main():
    for attempt in range(5):
        try:
            logger.info("^_> trying to start bot...")
            await dp.start_polling(bot)
            break
        except TelegramNetworkError as e:
            logger.error("network is not yet ready. waiting 3 sec..")
            await asyncio.sleep(3)
    else:
        logger.critical("couldn't connect to telegram after 5 retries.")



if __name__ == "__main__":
    asyncio.run(main())
