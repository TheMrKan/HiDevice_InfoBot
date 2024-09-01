from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from aiogram import Bot, html
import logging
import json

from core import controllers


session_factory: async_sessionmaker | None = None
bot: Bot | None = None

logger = logging.getLogger(__name__)


async def broadcast_async(mqtt_user: str, message: str):
    if not session_factory:
        raise RuntimeError("'session_factory' is not set")
    if not bot:
        raise RuntimeError("'bot' is not set")

    async with session_factory() as session:
        try:
            controller = await controllers.get_controller_async(session, mqtt_user)
            if not controller:
                raise KeyError(f"Controller {controller.mqtt_password!r} not found")

            users = await controllers.get_controller_users_async(session, controller)
            for user_id in users:
                logger.info("[%s] >>> [%s]: %s", controller.mqtt_user, user_id, json.dumps(message, ensure_ascii=False))
                await bot.send_message(user_id, message)

            await session.commit()
        except:
            await session.rollback()
        finally:
            await session.close()
