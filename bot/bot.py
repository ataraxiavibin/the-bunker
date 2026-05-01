# bot.py
#
# a Telegram bot that I can touch, to use with the bunker system
# cool but useless idea! i'm in.

import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.enums.dice_emoji import DiceEmoji

from services.berserk_checker import checker

TEST_BOTAPI = "8251338916:AAH86YwTeqaF44xv-bhW1EiLFgyR3j18ac0"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TEST_BOTAPI)
dp= Dispatcher()

@dp.message(Command("chapter"))
async def cmd_chapter(message: types.Message):
    result = checker.check(destination="bot")
    await message.reply(f"{result["message"]} Current chapter: {result["chapter"]}.")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())




