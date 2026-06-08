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
from aiogram.filters.command import Command
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

    data = response.json()
    
    await message.reply(f"{data["message"]} Current chapter: {data["chapter"]}.")


@dp.message(F.text.lower() == "check bunker connection")
async def check_connection(message: types.Message):
    result = await asyncio.to_thread(is_bunker_alive)

    if result:
        await message.reply("Running!")
    else: 
        await message.reply("Currently off.")

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
