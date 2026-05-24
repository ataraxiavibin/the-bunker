# bot.py
#
# a Telegram bot that I can touch, to use with the bunker system
# cool but useless idea! i'm in.

import os
import asyncio
import logging
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram import F

from services.berserk_checker import checker
from shared.connection import is_bunker_alive

load_dotenv()
tokenbot = os.environ.get("TEST_BOTAPI") 

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
    result = await asyncio.to_thread(checker.check, destination="bot")  # this is not good, because:
                                                                        # breaks the whole philosophy of a "one entry, one exit" system
                                                                        # but it works right now, so i'll change it when i'll make bunker.py a real entrance, not just an exit.
    await message.reply(f"{result["message"]} Current chapter: {result["chapter"]}.")


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
