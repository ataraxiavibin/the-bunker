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

from services.berserk_checker import checker

load_dotenv()
tokenbot = os.environ.get("TEST_BOTAPI") 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=tokenbot)
dp= Dispatcher()


@dp.message(Command("chapter"))
async def cmd_chapter(message: types.Message):
    result = checker.check(destination="bot")
    await message.reply(f"{result["message"]} Current chapter: {result["chapter"]}.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
