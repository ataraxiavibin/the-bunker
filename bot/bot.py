# bot.py
#
# a Telegram bot that I can touch, to use with the bunker system
# cool but useless idea! i'm in.

import os
import time
import asyncio
import logging
import json
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from shared.connection import is_system_up
from shared.transmitter import call_to_bunker
from shared.models import Call, Target

NAME = "telegram_bot"

load_dotenv()
tokenbot = os.environ.get("BOT_API") 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=tokenbot, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp= Dispatcher()

def format_cli(text: str) -> str:
    return f"<pre>{text}</pre>" #TODO: make a decision

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    msg = (
        "bunkerOS v0.1a :: (telegram-tty1)\n\n"

        "auth ok. still standing by.\n\n"

        "/help available.\n"
    )

    await message.answer(
        format_cli(msg),
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    msg = (
        "+-- [ bunkerOS :: help manual ] --+\n"
        "|\n"
        "|-- /bunker   :: get system status\n"
        "|-- /pods     :: control pods connectivity\n"
        "|   +-- args: [connect, disconnect, reconnect]\n"
        "|-- /chapter  :: check berserk chapter release\n"
        "|\n"
        "+-- ready.\n"
    )

    await message.answer(
        format_cli(msg)
    )


@dp.message(Command("chapter"))
async def cmd_chapter(message: types.Message):
    exec_msg = "^_> executing...\n"
    sent_msg = await message.reply(format_cli(exec_msg))
    start_time = time.perf_counter()

    action = "check"
    call = Call(
        caller=NAME,
        target=Target(
            service="berserk_checker",
            action=action
        )
    )
    response = await call_to_bunker(call) 
    latency = int((time.perf_counter() - start_time) * 1000)

    if not response:
        msg = f"bunkerOS :: err\n~~ {latency} ms.\n\nno response, cannot confirm."
        await sent_msg.edit_text(format_cli(msg))
        return

    data = response.json()
    msg = f"~~ {data["message"].lower()}\n~~ current chapter: {data["chapter"]}."
    
    await sent_msg.edit_text(format_cli(msg))


@dp.message(Command("pods"))
async def cmd_pods(message: types.Message, command: CommandObject):
    start_time = time.perf_counter()
    action = command.args

    valid_actions = ["connect", "disconnect", "reconnect"]

    if not action or action not in valid_actions:
        msg = f"bunkerOS :: err\n\nunknown arg. /help."
        return await message.reply(format_cli(msg))

    call = Call(
        caller=NAME,
        target=Target(
            service="pods_connect",
            action=action
        )
    )

    response = await call_to_bunker(call) 
    latency = int((time.perf_counter() - start_time) * 1000)
    if not response:
        msg = f"bunkerOS :: err\n~~ {latency} ms.\n\nno response, cannot confirm."
        await message.reply(format_cli(msg))

    data = response.json()
    msg = f"~~ {data["message"].lower()}"
        
    await message.reply(format_cli(msg)) # TODO:


@dp.message(Command("bunker", "status", "c"))
@dp.message(F.text.lower() == "check bunker connection")
async def check_connection(message: types.Message):
    start_time = time.perf_counter()
    result = await is_system_up()
    latency = int((time.perf_counter() - start_time) * 1000)

    msg = f"~~ routing...\n~~ {latency} ms.\n\nnodes:\n"
    max_len_key = max(len(key) for key in result.keys())

    for key, is_up in result.items():
        if is_up:
            msg += f"- [x] {key:<{max_len_key}} :: intact\n"
        else:
            msg += f"- [#] {key:<{max_len_key}} :: connection failed\n" 
        # maybe in future do it like that: :: intact (xx ms);

    await message.reply(format_cli(msg))


@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    empty_lines = "\n" * 45
    stretcher = "\xa0" * 60

    msg = f"{stretcher}{empty_lines}" + "\n~_>|"

    await message.reply(format_cli(msg))

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
