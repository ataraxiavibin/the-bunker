# bot.py
#
# a Telegram bot that I can touch, to use with the bunker system
# cool but useless idea! i'm in.

import os
import asyncio
import logging
import json
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram import F

from shared.connection import is_bunker_alive
from shared.transmitter import call_to_bunker

NAME = "telegram_bot"

load_dotenv()
tokenbot = os.environ.get("BOT_API") 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=tokenbot)
dp= Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="Check Bunker connection")]
    ]

    keyboard=types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Was darf's sein?"
    )

    await message.answer("Welcome.", reply_markup=keyboard)


@dp.message(Command("chapter"))
async def cmd_chapter(message: types.Message):
    response = await call_to_bunker(
        NAME,
        {
            "service": "berserk_checker",
            "action": "check"
        }
    )

    if not response:
        return await message.reply(f"Failed to reach the system. Call may are may not have been ran.")

    data = response.json()
    
    await message.reply(f"{data["message"]} Current chapter: {data["chapter"]}.")

@dp.message(Command("pods"))
async def cmd_pods(message: types.Message, command: CommandObject):
    action = command.args

    valid_actions = ["connect", "disconnect", "reconnect"]

    if not action or action not in valid_actions:
         return await message.reply(f"Provide a valid action: {', '.join(valid_actions)}")

    response = await call_to_bunker(
        NAME,
        {
            "service": "pods_connect",
            "action": action
        }
    )
    if not response:
        return await message.reply(f"Failed to reach the system. Call may are may not have been ran.")

    data = response.json()
        
    await message.reply(f"{data["message"]}")



@dp.message(Command("bunker", "status", "c"))
@dp.message(F.text.lower() == "check bunker connection")
async def check_connection(message: types.Message):
    result = await is_bunker_alive()

    if result:
        await message.reply("Running!")
    else: 
        await message.reply("Currently off.")

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
