import asyncio
import logging
import logging.config
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from sqlalchemy.ext.asyncio import async_sessionmaker

import config

if not os.path.isdir("logs"):
    os.mkdir("logs")
logging.config.dictConfig(config.LOGGING)
logger = logging.getLogger(__name__)


from middlewares import DbSessionMiddleware, UsersMiddleware
import commands
from core.db import engine
import broadcaster
import mqtt


async def main():
    logger.info("Starting...")

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    await bot.set_my_commands(commands=[
        BotCommand(command="/list", description="Список подключенных контроллеров"),
        BotCommand(command="/add_controller", description="Подключить контроллер"),
        BotCommand(command="/remove_controller", description="Удалить контроллер")
    ])

    broadcaster.session_factory = sessionmaker
    broadcaster.bot = bot

    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker))
    dp.message.middleware(UsersMiddleware())

    dp.include_router(commands.router)

    listen_task = asyncio.create_task(mqtt.listen_async(config.MQTT_HOST, config.MQTT_PORT, config.MQTT_USER, config.MQTT_PASSWORD))
    if all((config.RESERVE_MQTT_HOST, config.RESERVE_MQTT_PORT, config.RESERVE_MQTT_USER, config.RESERVE_MQTT_PASSWORD)):
        listen_reserver_task = asyncio.create_task(mqtt.listen_async(config.RESERVE_MQTT_HOST, config.RESERVE_MQTT_PORT, config.RESERVE_MQTT_USER, config.RESERVE_MQTT_PASSWORD))
    else:
        logger.info("Reserve MQTT server is not configured")

    logger.info("Polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    # https://pypi.org/project/asyncio-mqtt/#note-for-windows-users
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

