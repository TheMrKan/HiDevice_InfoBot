import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from sqlalchemy.ext.asyncio import async_sessionmaker

import config
from middlewares import DbSessionMiddleware, UsersMiddleware
import commands
from core.db import engine
import broadcaster
import mqtt


async def main():

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    await bot.set_my_commands(commands=[
        BotCommand(command="/list", description="Список подключенных контроллеров"),
        BotCommand(command="/add_controller", description="Подключить контроллер")
    ])

    broadcaster.session_factory = sessionmaker
    broadcaster.bot = bot

    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker))
    dp.message.middleware(UsersMiddleware())

    dp.include_router(commands.router)

    task = asyncio.create_task(mqtt.listen_async())

    await dp.start_polling(bot)


if __name__ == "__main__":
    # https://pypi.org/project/asyncio-mqtt/#note-for-windows-users
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

