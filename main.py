import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from sqlalchemy.ext.asyncio import async_sessionmaker

import config
from middlewares import DbSessionMiddleware, UsersMiddleware
import commands
from core.db import engine


async def main():

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    await bot.set_my_commands(commands=[
        BotCommand(command="/add_controller", description="Подключить контроллер")
    ])

    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker))
    dp.message.middleware(UsersMiddleware())

    dp.include_router(commands.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

